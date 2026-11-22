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
        self.model = self.load_model()
        self.pending_action = None
        self.stop_requested = False
        self.listener = Listener(on_press=self.on_key_press)
        self.listener.start()

    def on_key_press(self, key) -> None:
        if key == STOP_KEY:
            self.stop_requested = True
            return False

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
        """Detect the large single Play/Retry button in the lower center."""
        height, width = frame.shape[:2]
        hsv = self.hsv(frame)
        mask = cv2.inRange(hsv, ORANGE_LOW, ORANGE_HIGH)

        x1, x2 = int(width * 0.40), int(width * 0.60)
        y1, y2 = int(height * 0.68), int(height * 0.86)
        roi = mask[y1:y2, x1:x2]
        if roi.size == 0:
            return False

        orange_ratio = cv2.countNonZero(roi) / float(roi.size)
        return orange_ratio > 0.45

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
            print("[INFO] Loading pretrained DQN checkpoint...", flush=True)
            model = DQN.load(str(MODEL_FILE), env=env, device="auto")
            if REPLAY_FILE.exists():
                try:
                    model.load_replay_buffer(str(REPLAY_FILE))
                    print("[INFO] Previous experience replay buffer loaded.", flush=True)
                except Exception as exc:
                    print(f"[WARN] Could not load replay buffer: {exc}", flush=True)
        else:
            print("[INFO] Creating a new DQN agent with an initial safe-side heuristic.", flush=True)
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
        for _ in range(80):
            if self.bot.stop_requested:
                break
            frame = self.bot.capture()
            if self.bot.start_or_retry_button_visible(frame):
                self.bot.click_play_or_retry()
                continue
            obs = self.observe(frame)
            if obs[0] != 0.0:
                self.last_observation = obs
                self.episode_steps = 0
                return obs, {}
            time.sleep(0.1)
        self.last_observation = np.zeros(2, dtype=np.float32)
        return self.last_observation, {}

    def step(self, action):
        side = "left" if int(action) == 0 else "right"
        self.bot.press(side)
        time.sleep(ACTION_INTERVAL)
        frame = self.bot.capture()

        if self.bot.start_or_retry_button_visible(frame) and self.bot.detect_player_side(frame) is None:
            reward = -5.0
            terminated = True
            self.episode_steps = 0
            self.log_reward(reward, "death detected", side)
            self.bot.click_play_or_retry()
            next_obs = np.zeros(2, dtype=np.float32)
        else:
            next_obs = self.observe(frame)
            if next_obs[0] != 0.0:
                reward = 1.0
                terminated = False
                self.episode_steps += 1
                self.log_reward(reward, "survived move", side)
            else:
                reward = 0.0
                terminated = False
        self.last_observation = next_obs
        return next_obs, reward, terminated, False, {}

    def log_reward(self, reward: float, outcome: str, action: str) -> None:
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "reward": int(reward),
            "outcome": outcome,
        }
        with TRAINING_LOG.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry) + "\\n")
        print(f"[LEARN] {outcome}: {reward:+.0f} chocolates", flush=True)

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
