from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import time
from dataclasses import dataclass

import cv2
import mss
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import BaseCallback
import pyautogui
import pygetwindow as gw
from pynput.keyboard import Controller, Key, Listener


WINDOW_PATTERN = re.compile(r"lumber\s*jack", re.IGNORECASE)
STOP_KEY = Key.esc

ACTION_INTERVAL = 0.16
LOOP_DELAY = 0.025
MODEL_FILE = Path(__file__).with_name("lumberjack_dqn.zip")
REPLAY_FILE = Path(__file__).with_name("lumberjack_replay_buffer.pkl")
TRAINING_LOG = Path(__file__).with_name("training_log.jsonl")
CHOCOLATE_FILE = Path(__file__).with_name("chocolate_balance.json")

# HSV ranges tuned from the supplied game screenshots.
GREEN_LOW = np.array([35, 60, 70], dtype=np.uint8)
GREEN_HIGH = np.array([90, 255, 255], dtype=np.uint8)
RED_LOW_1 = np.array([0, 100, 70], dtype=np.uint8)
RED_HIGH_1 = np.array([10, 255, 255], dtype=np.uint8)
RED_LOW_2 = np.array([170, 100, 70], dtype=np.uint8)
RED_HIGH_2 = np.array([179, 255, 255], dtype=np.uint8)
ORANGE_LOW = np.array([5, 60, 70], dtype=np.uint8)
ORANGE_HIGH = np.array([30, 255, 255], dtype=np.uint8)


@dataclass
class GameWindow:
    title: str
    left: int
    top: int
    width: int
    height: int

    @property
    def region(self) -> dict:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


class LumberJackBot:
    def __init__(self) -> None:
        self.keyboard = Controller()
        self.sct = mss.MSS()
        self.window: GameWindow | None = None
        self.last_action = 0.0
        self.last_state_message = ""
        self.chocolates = self.load_chocolates()
        self.stop_requested = False
        self.listener = Listener(on_press=self.on_key_press)
        self.listener.start()

    def on_key_press(self, key) -> None:
        if key == STOP_KEY:
            self.stop_requested = True
            return False

    def load_chocolates(self) -> int:
        try:
            return int(json.loads(CHOCOLATE_FILE.read_text(encoding="utf-8")).get("total", 0))
        except (OSError, ValueError, json.JSONDecodeError):
            return 0

    def find_window(self) -> GameWindow:
        visible_windows = []
        lumberjack_matches = []
        telegram_matches = []

        for win in gw.getAllWindows():
            title = (win.title or "").strip()
            if win.width < 220 or win.height < 300 or win.isMinimized:
                continue
            if title:
                visible_windows.append(title)
            if WINDOW_PATTERN.search(title):
                lumberjack_matches.append(win)
            elif "telegram" in title.lower():
                telegram_matches.append(win)

        # Telegram Desktop often keeps the Mini App inside a window titled
        # "Telegram", not "LumberJack". Prefer an exact game-title match,
        # then fall back to the Telegram window.
        matches = lumberjack_matches or telegram_matches

        if not matches:
            titles = ", ".join(visible_windows[:12]) or "No visible titled windows"
            raise RuntimeError(
                "Could not find a LumberJack or Telegram window. "
                f"Visible windows: {titles}. Open the Mini App in Telegram Desktop."
            )

        win = max(matches, key=lambda item: item.width * item.height)
        return GameWindow(win.title, win.left, win.top, win.width, win.height)

    def capture(self) -> np.ndarray:
        assert self.window is not None
        shot = self.sct.grab(self.window.region)
        return cv2.cvtColor(np.asarray(shot), cv2.COLOR_BGRA2BGR)

    @staticmethod
    def hsv(frame: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    def start_or_retry_button_visible(self, frame: np.ndarray) -> bool:
        """
        Detect the circular wood-colored restart button shown on the score screen.
        The character remains visible on that screen, so this detector must not
        depend on the player sprite disappearing.
        """
        height, width = frame.shape[:2]
        hsv = self.hsv(frame)

        # The restart button is a large tan/orange circle near the lower center.
        # Use a slightly wider hue/saturation range than the old detector.
        low = np.array([5, 45, 100], dtype=np.uint8)
        high = np.array([32, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, low, high)

        x1, x2 = int(width * 0.32), int(width * 0.68)
        y1, y2 = int(height * 0.62), int(height * 0.90)
        roi = mask[y1:y2, x1:x2]
        if roi.size == 0:
            return False

        # Look for a substantial connected warm-colored region, not just a
        # few orange pixels from the score/coin decorations.
        count, _, stats, _ = cv2.connectedComponentsWithStats(roi, connectivity=8)
        min_area = int(width * height * 0.008)
        for index in range(1, count):
            x, y, w, h, area = stats[index]
            if area < min_area:
                continue
            aspect = w / float(max(h, 1))
            if 0.65 <= aspect <= 1.45 and w >= width * 0.12 and h >= height * 0.10:
                return True

        # Fallback for a textured circle whose rings split into components.
        ratio = cv2.countNonZero(roi) / float(roi.size)
        return ratio > 0.16

    def detect_player_side(self, frame: np.ndarray) -> str | None:
        """Find the red-shirt player and return the side of the tree they occupy."""
        height, width = frame.shape[:2]
        hsv = self.hsv(frame)
        red1 = cv2.inRange(hsv, RED_LOW_1, RED_HIGH_1)
        red2 = cv2.inRange(hsv, RED_LOW_2, RED_HIGH_2)
        mask = cv2.bitwise_or(red1, red2)

        x1, x2 = int(width * 0.15), int(width * 0.85)
        y1, y2 = int(height * 0.32), int(height * 0.62)
        roi = mask[y1:y2, x1:x2]
        count, _, stats, _ = cv2.connectedComponentsWithStats(roi, connectivity=8)

        min_area = int(width * height * 0.0015)
        candidates = []
        for index in range(1, count):
            x, y, w, h, area = stats[index]
            if area >= min_area and h >= height * 0.035:
                candidates.append((area, x + w / 2 + x1))

        if not candidates:
            return None

        _, player_x = max(candidates)
        return "left" if player_x < width / 2 else "right"

    def detect_nearest_branch_side(self, frame: np.ndarray) -> str | None:
        """Find the lowest visible green branch, ignoring the green ground."""
        height, width = frame.shape[:2]
        hsv = self.hsv(frame)
        mask = cv2.inRange(hsv, GREEN_LOW, GREEN_HIGH)

        # Branches are above the grass platform in the supplied game layout.
        y1, y2 = int(height * 0.10), int(height * 0.42)
        roi = mask[y1:y2, :]
        count, _, stats, _ = cv2.connectedComponentsWithStats(roi, connectivity=8)

        min_area = int(width * height * 0.003)
        min_branch_width = int(width * 0.16)
        candidates = []

        for index in range(1, count):
            x, y, w, h, area = stats[index]
            if area < min_area or w < min_branch_width or h < height * 0.025:
                continue
            center_x = x + w / 2
            bottom_y = y + h + y1
            side = "left" if center_x < width / 2 else "right"
            candidates.append((bottom_y, side))

        if not candidates:
            return None

        # The branch closest to the player is the lowest branch on screen.
        return max(candidates, key=lambda item: item[0])[1]

    def click_play_or_retry(self) -> None:
        assert self.window is not None
        x = self.window.left + int(self.window.width * 0.50)
        y = self.window.top + int(self.window.height * 0.77)
        pyautogui.click(x, y)
        # Move away from the game without touching a screen corner.
        screen_width, screen_height = pyautogui.size()
        safe_x = max(1, screen_width - 60)
        safe_y = max(1, screen_height - 60)
        pyautogui.moveTo(safe_x, safe_y, duration=0.05)
        print("[INFO] Play/Retry button detected. Starting automatically.", flush=True)
        time.sleep(1.2)

    def press(self, side: str) -> None:
        key = Key.left if side == "left" else Key.right
        self.keyboard.press(key)
        self.keyboard.release(key)
        self.last_action = time.monotonic()

    def run(self) -> None:
        print("[INFO] Switch to the LumberJack game window. Starting in 5 seconds...", flush=True)
        for remaining in range(5, 0, -1):
            if self.stop_requested:
                print("[STOP] Bot stopped.", flush=True)
                return
            print(f"[INFO] Starting in {remaining}...", flush=True)
            time.sleep(1)

        self.window = self.find_window()
        print(
            f"[OK] Game window found: {self.window.title} "
            f"({self.window.width}x{self.window.height})",
            flush=True,
        )
        env = LumberJackEnv(self)
        if MODEL_FILE.exists():
            print("[INFO] Loading saved DQN checkpoint...", flush=True)
            model = DQN.load(str(MODEL_FILE), env=env, device="auto")
            if REPLAY_FILE.exists():
                try:
                    model.load_replay_buffer(str(REPLAY_FILE))
                    print("[INFO] Previous experience replay buffer loaded.", flush=True)
                except Exception as exc:
                    print(f"[WARN] Could not load replay buffer: {exc}", flush=True)
        else:
            print("[INFO] Creating DQN agent with a built-in branch-avoidance starter strategy.", flush=True)
            model = DQN(
                "MlpPolicy",
                env,
                learning_rate=1e-3,
                buffer_size=20000,
                learning_starts=30,
                batch_size=32,
                train_freq=1,
                gradient_steps=1,
                exploration_fraction=0.20,
                exploration_initial_eps=0.80,
                exploration_final_eps=0.05,
                policy_kwargs={"net_arch": [64, 64]},
                verbose=0,
                device="auto",
            )

        print("[INFO] DQN training and automatic play are running. Press Esc to stop.", flush=True)
        callback = StopOnEscape(self)
        try:
            while not self.stop_requested:
                model.learn(total_timesteps=256, reset_num_timesteps=False, callback=callback)
                model.save(str(MODEL_FILE))
                try:
                    model.save_replay_buffer(str(REPLAY_FILE))
                except Exception as exc:
                    print(f"[WARN] Could not save replay buffer: {exc}", flush=True)
                print(f"[SAVE] DQN checkpoint saved | Timesteps: {model.num_timesteps}", flush=True)
        finally:
            model.save(str(MODEL_FILE))
            try:
                model.save_replay_buffer(str(REPLAY_FILE))
            except Exception:
                pass
            env.close()
        print("[STOP] Bot stopped.", flush=True)

    def set_state_message(self, message: str) -> None:
        if message != self.last_state_message:
            print(f"[INFO] {message}", flush=True)
            self.last_state_message = message

    def close(self) -> None:
        self.stop_requested = True
        self.listener.stop()
        self.sct.close()



class LumberJackEnv(gym.Env):
    """Gymnasium adapter: observations come from the game screen; rewards come from survival."""
    metadata = {"render_modes": []}

    def __init__(self, bot: LumberJackBot):
        super().__init__()
        self.bot = bot
        self.action_space = spaces.Discrete(2)  # 0 = left, 1 = right
        self.observation_space = spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
        self.last_observation = np.zeros(2, dtype=np.float32)
        self.episode_steps = 0

    @staticmethod
    def side_value(side: str | None) -> float:
        if side == "left":
            return -1.0
        if side == "right":
            return 1.0
        return 0.0

    def observe(self, frame: np.ndarray) -> np.ndarray:
        player = self.bot.detect_player_side(frame)
        branch = self.bot.detect_nearest_branch_side(frame)
        return np.array([self.side_value(player), self.side_value(branch)], dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        clicked_retry = False
        for _ in range(80):
            if self.bot.stop_requested:
                break
            frame = self.bot.capture()
            if self.bot.start_or_retry_button_visible(frame):
                if not clicked_retry:
                    self.bot.click_play_or_retry()
                    clicked_retry = True
                time.sleep(0.15)
                continue
            obs = self.observe(frame)
            if obs[0] != 0.0:
                self.last_observation = obs
                self.episode_steps = 0
                return obs, {}
            time.sleep(0.1)
        if self.bot.stop_requested:
            raise RuntimeError("Bot stopped while waiting for a playable game screen.")
        raise RuntimeError(
            "Could not confirm that the game is playable. Check the game window and detection colors."
        )

    def choose_action_with_game_knowledge(self, action: int) -> tuple[int, str]:
        """
        Starter strategy: avoid the side containing the nearest visible branch.
        DQN still chooses when no branch is confidently detected.
        """
        branch_value = float(self.last_observation[1])
        if branch_value < -0.5:
            return 1, "starter rule: branch on left, move right"
        if branch_value > 0.5:
            return 0, "starter rule: branch on right, move left"
        return int(action), "DQN choice: no branch confidently detected"

    def step(self, action):
        selected_action, decision_reason = self.choose_action_with_game_knowledge(int(action))
        side = "left" if selected_action == 0 else "right"
        self.bot.set_state_message(f"{decision_reason}; moving {side}.")
        self.bot.press(side)
        time.sleep(ACTION_INTERVAL)
        frame = self.bot.capture()

        button_visible = self.bot.start_or_retry_button_visible(frame)
        player_side = self.bot.detect_player_side(frame)

        if button_visible:
            # On the score screen the lumberjack character is still drawn,
            # so the restart button itself is the death/game-over signal.
            reward = -5.0
            terminated = True
            self.episode_steps = 0
            self.log_reward(reward, "score screen / restart button detected", side)
            self.bot.click_play_or_retry()
            next_obs = np.zeros(2, dtype=np.float32)
        elif player_side is not None and not button_visible:
            # Survival is credited only when the player is visible and no
            # Play/Retry screen is detected after the action.
            next_obs = self.observe(frame)
            reward = 1.0
            terminated = False
            self.episode_steps += 1
            self.log_reward(reward, "player visible after move", side)
        else:
            # Ambiguous screen: do not teach the model that this was a success
            # or a death. Keep the transition reward neutral.
            next_obs = self.observe(frame)
            reward = 0.0
            terminated = False
            self.bot.set_state_message("Game state uncertain; no chocolate reward assigned.")

        self.last_observation = next_obs
        return next_obs, reward, terminated, False, {}

    def log_reward(self, reward: float, outcome: str, action: str) -> None:
        self.bot.chocolates += int(reward)
        CHOCOLATE_FILE.write_text(
            json.dumps({"total": self.bot.chocolates}, indent=2),
            encoding="utf-8",
        )
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "reward": int(reward),
            "outcome": outcome,
            "chocolates_total": self.bot.chocolates,
        }
        with TRAINING_LOG.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry) + "\n")
        print(
            f"[LEARN] {outcome}: {reward:+.0f} chocolates | "
            f"Balance: {self.bot.chocolates}",
            flush=True,
        )

    def close(self):
        return None


class StopOnEscape(BaseCallback):
    def __init__(self, bot: LumberJackBot):
        super().__init__(verbose=0)
        self.bot = bot

    def _on_step(self) -> bool:
        return not self.bot.stop_requested

def main() -> int:
    bot = LumberJackBot()
    try:
        bot.run()
        return 0
    except KeyboardInterrupt:
        print("\n[STOP] Stopped.", flush=True)
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        bot.close()


if __name__ == "__main__":
    raise SystemExit(main())
