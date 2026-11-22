from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path
import time
from dataclasses import dataclass

import cv2
import mss
import numpy as np
import pyautogui
import pygetwindow as gw
from pynput.keyboard import Controller, Key, Listener


WINDOW_PATTERN = re.compile(r"lumber\s*jack", re.IGNORECASE)
STOP_KEY = Key.esc

ACTION_INTERVAL = 0.16
LOOP_DELAY = 0.025
MODEL_FILE = Path(__file__).with_name("chocolate_model.json")
TRAINING_LOG = Path(__file__).with_name("training_log.jsonl")
LEARNING_RATE = 0.25
EPSILON = 0.12

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

    def load_model(self) -> dict:
        if MODEL_FILE.exists():
            try:
                data = json.loads(MODEL_FILE.read_text(encoding="utf-8"))
                data.setdefault("chocolates", 0)
                data.setdefault("successful_actions", 0)
                data.setdefault("deaths", 0)
                data.setdefault("q_values", {})
                return data
            except (OSError, json.JSONDecodeError):
                print("[WARN] Could not read saved model; creating a fresh one.", flush=True)

        data = {
            "version": 1,
            "chocolates": 0,
            "successful_actions": 0,
            "deaths": 0,
            "q_values": {},
            "initial_knowledge": {
                "state_features": ["player_side", "nearest_branch_side"],
                "actions": ["left", "right"],
                "prior_rule": "Prefer the side opposite the nearest branch.",
                "reward_rule": "Survived move: +1 chocolate; detected death: -5 chocolates."
            }
        }
        self.model = data
        self.save_model()
        return data

    def save_model(self) -> None:
        temp = MODEL_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(self.model, indent=2), encoding="utf-8")
        temp.replace(MODEL_FILE)

    def learn(self, reward: int, outcome: str) -> None:
        if self.pending_action is None:
            return
        state, action = self.pending_action
        values = self.model["q_values"].setdefault(state, {})
        old = values.get(action, 0.0)
        values[action] = old + 0.25 * (reward - old)
        self.model["chocolates"] += reward
        if reward > 0:
            self.model["successful_actions"] += 1
        else:
            self.model["deaths"] += 1

        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "state": state, "action": action, "reward": reward,
            "outcome": outcome, "chocolates_total": self.model["chocolates"],
            "q_value": round(values[action], 4)
        }
        with TRAINING_LOG.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry) + "\n")
        self.save_model()
        print(
            f"[LEARN] {outcome}: {reward:+d} chocolates | "
            f"Total: {self.model['chocolates']} | "
            f"Moves: {self.model['successful_actions']} | Deaths: {self.model['deaths']}",
            flush=True
        )
        self.pending_action = None

    def choose_action(self, player_side: str, branch_side: str) -> tuple[str, str]:
        state = f"player={player_side}|branch={branch_side}"
        values = self.model["q_values"].setdefault(state, {})
        preferred = "right" if branch_side == "left" else "left"
        values.setdefault(preferred, 0.5)
        values.setdefault("left" if preferred == "right" else "right", -0.25)
        if random.random() < 0.12:
            action = random.choice(["left", "right"])
        else:
            action = max(["left", "right"], key=lambda key: values.get(key, 0.0))
        return state, action

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
        print("[INFO] Automatic detection is running. Press Esc to stop.", flush=True)

        while not self.stop_requested:
            try:
                current = self.find_window()
                self.window = current
            except RuntimeError:
                time.sleep(0.3)
                continue

            frame = self.capture()

            player_side = self.detect_player_side(frame)
            game_over_visible = self.start_or_retry_button_visible(frame)

            if game_over_visible and player_side is None:
                self.learn(-5, "death detected")
                self.click_play_or_retry()
                continue

            if player_side is not None and self.pending_action is not None:
                self.learn(+1, "survived previous move")

            if game_over_visible:
                self.click_play_or_retry()
                continue

            branch_side = self.detect_nearest_branch_side(frame)

            if player_side is None:
                self.set_state_message("Waiting for the game screen...")
                time.sleep(LOOP_DELAY)
                continue

            if branch_side is None:
                self.set_state_message("Player detected; waiting for a branch...")
                time.sleep(LOOP_DELAY)
                continue

            state, target_side = self.choose_action(player_side, branch_side)

            if time.monotonic() - self.last_action >= ACTION_INTERVAL:
                self.press(target_side)
                self.pending_action = (state, target_side)
                self.set_state_message(
                    f"Player: {player_side} | Nearest branch: {branch_side} | "
                    f"Model chooses: {target_side}"
                )

            time.sleep(LOOP_DELAY)

        print("[STOP] Bot stopped.", flush=True)

    def set_state_message(self, message: str) -> None:
        if message != self.last_state_message:
            print(f"[INFO] {message}", flush=True)
            self.last_state_message = message

    def close(self) -> None:
        self.stop_requested = True
        self.listener.stop()
        self.sct.close()


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
