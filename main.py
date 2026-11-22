from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass

import cv2
import mss
import numpy as np
import pyautogui
import pygetwindow as gw
import pytesseract
from pynput.keyboard import Controller, Key, Listener


WINDOW_PATTERN = re.compile(r"lumber\s*jack", re.IGNORECASE)
BUTTON_WORDS = {"play", "start", "replay", "again", "continue"}
STOP_KEY = Key.esc


@dataclass
class GameWindow:
    title: str
    left: int
    top: int
    width: int
    height: int

    @property
    def region(self) -> dict:
        return {"left": self.left, "top": self.top,
                "width": self.width, "height": self.height}


class LumberJackBot:
    def __init__(self) -> None:
        self.keyboard = Controller()
        self.sct = mss.mss()
        self.window: GameWindow | None = None
        self.direction: str | None = None
        self.last_action = 0.0
        self.action_interval = 0.095
        self.stop_requested = False
        self.listener = Listener(on_press=self.on_key_press)
        self.listener.start()

    def on_key_press(self, key) -> None:
        if key == STOP_KEY:
            self.stop_requested = True
            return False

    def find_window(self) -> GameWindow:
        matches = []
        for win in gw.getAllWindows():
            if win.width < 220 or win.height < 300:
                continue
            if WINDOW_PATTERN.search(win.title or ""):
                matches.append(win)
        if not matches:
            raise RuntimeError(
                'پنجره‌ای با عنوان شامل "LumberJack" پیدا نشد. '
                "اول Mini App بازی را در Telegram Desktop باز کن."
            )
        win = max(matches, key=lambda item: item.width * item.height)
        if win.isMinimized:
            raise RuntimeError("پنجره بازی minimize شده؛ آن را باز کن.")
        return GameWindow(win.title, win.left, win.top, win.width, win.height)

    def capture(self) -> np.ndarray:
        assert self.window is not None
        shot = self.sct.grab(self.window.region)
        return cv2.cvtColor(np.asarray(shot), cv2.COLOR_BGRA2BGR)

    @staticmethod
    def brown_mask(frame: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, np.array([3, 55, 35]), np.array([28, 255, 220]))

    @staticmethod
    def find_tree_center(wood: np.ndarray) -> int | None:
        h, w = wood.shape
        x1, x2 = int(w * 0.25), int(w * 0.75)
        y1, y2 = int(h * 0.20), int(h * 0.90)
        scores = (wood[y1:y2, x1:x2] > 0).sum(axis=0)
        if scores.size == 0:
            return None
        idx = int(np.argmax(scores))
        if int(scores[idx]) < h * 0.12:
            return None
        return x1 + idx

    @staticmethod
    def find_player_head(frame: np.ndarray, tree_x: int) -> tuple[str, int] | None:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([78, 12, 175]), np.array([112, 180, 255]))
        h, w = mask.shape
        mask[:int(h * 0.42), :] = 0
        count, _, stats, centers = cv2.connectedComponentsWithStats(mask, 8)
        candidates = []
        for i in range(1, count):
            x, y, cw, ch, area = stats[i]
            cx, cy = centers[i]
            if area < 12 or area > 2200 or ch < 3:
                continue
            if abs(cx - tree_x) < w * 0.025 or cy > h * 0.94:
                continue
            score = area - abs(cy - h * 0.73) * 0.08
            candidates.append((score, "left" if cx < tree_x else "right", int(cy)))
        if not candidates:
            return None
        _, side, y = max(candidates, key=lambda item: item[0])
        return side, y

    @staticmethod
    def branch_on_side(wood: np.ndarray, tree_x: int, head_y: int, side: str) -> bool:
        h, w = wood.shape
        band = max(5, int(h * 0.012))
        y1, y2 = max(0, head_y - band), min(h, head_y + band + 1)
        reach, gap = int(w * 0.24), max(5, int(w * 0.035))
        if side == "left":
            x1, x2 = max(0, tree_x - reach), max(0, tree_x - gap)
        else:
            x1, x2 = min(w, tree_x + gap), min(w, tree_x + reach)
        if x2 <= x1:
            return False
        row = wood[y1:y2, x1:x2]
        threshold = max(7, int((x2 - x1) * 0.10))
        return int((row > 0).sum()) >= threshold

    def find_text_button(self, frame: np.ndarray) -> tuple[int, int] | None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        data = pytesseract.image_to_data(
            gray, config="--psm 11", output_type=pytesseract.Output.DICT
        )
        candidates = []
        for i, raw in enumerate(data["text"]):
            word = re.sub(r"[^a-z]", "", raw.lower())
            if word not in BUTTON_WORDS:
                continue
            try:
                confidence = float(data["conf"][i])
            except (TypeError, ValueError):
                confidence = 0
            if confidence < 35:
                continue
            x, y = int(data["left"][i]), int(data["top"][i])
            bw, bh = int(data["width"][i]), int(data["height"][i])
            candidates.append((confidence, (x + bw // 2, y + bh // 2)))
        if not candidates:
            return None
        return max(candidates, key=lambda item: item[0])[1]

    def click_button_if_present(self, frame: np.ndarray) -> bool:
        point = self.find_text_button(frame)
        if point is None:
            return False
        assert self.window is not None
        print(f"[AUTO] دکمه بازی تشخیص داده شد؛ کلیک در {point}")
        pyautogui.click(self.window.left + point[0], self.window.top + point[1])
        time.sleep(0.8)
        self.direction = None
        return True

    def press(self, side: str) -> None:
        key = Key.left if side == "left" else Key.right
        self.keyboard.press(key)
        self.keyboard.release(key)
        self.direction = side
        self.last_action = time.monotonic()

    def analyze_and_play(self, frame: np.ndarray) -> bool:
        wood = self.brown_mask(frame)
        tree_x = self.find_tree_center(wood)
        if tree_x is None:
            return False
        player = self.find_player_head(frame, tree_x)
        if player is None:
            return False
        side, head_y = player
        if self.direction is None:
            self.direction = side
        blocked = self.branch_on_side(wood, tree_x, head_y, self.direction)
        next_side = ("right" if self.direction == "left" else "left") if blocked else self.direction
        if time.monotonic() - self.last_action >= self.action_interval:
            self.press(next_side)
        return True

    def run(self) -> None:
        self.window = self.find_window()
        print(f"[OK] پنجره پیدا شد: {self.window.title}")
        print(f"[OK] اندازه پنجره: {self.window.width}x{self.window.height}")
        print("[INFO] برای توقف هر زمان کلید Esc را بزن.")
        while not self.stop_requested:
            try:
                self.window = self.find_window()
            except RuntimeError:
                time.sleep(0.3)
                continue
            frame = self.capture()
            if self.click_button_if_present(frame):
                continue
            if not self.analyze_and_play(frame):
                time.sleep(0.04)
            else:
                time.sleep(0.012)
        print("[STOP] بات متوقف شد.")

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
        print("\n[STOP] توقف با Ctrl+C")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    finally:
        bot.close()


if __name__ == "__main__":
    raise SystemExit(main())
