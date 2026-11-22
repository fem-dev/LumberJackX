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
from pynput.keyboard import Controller, Key, Listener


WINDOW_PATTERN = re.compile(r"lumber\s*jack", re.IGNORECASE)
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
        self.action_interval = 0.16
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
        threshold = max(10, int((x2 - x1) * 0.14))
        return int((row > 0).sum()) >= threshold

    @staticmethod
    def find_start_button(frame: np.ndarray) -> tuple[int, int] | None:
        """Find a prominent saturated rounded button without OCR or templates."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = hsv.shape[:2]
        # Start/replay buttons are usually saturated and near the center of the game.
        mask = cv2.inRange(hsv, np.array([0, 85, 75]), np.array([179, 255, 255]))
        y1, y2 = int(h * 0.20), int(h * 0.82)
        x1, x2 = int(w * 0.10), int(w * 0.90)
        roi = mask[y1:y2, x1:x2]
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 5))
        roi = cv2.morphologyEx(roi, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for contour in contours:
            bx, by, bw, bh = cv2.boundingRect(contour)
            area = bw * bh
            ratio = bw / max(1, bh)
            if area < w * h * 0.008 or bw < w * 0.25 or bh < h * 0.035:
                continue
            if not 1.4 <= ratio <= 6.5:
                continue
            fill = cv2.contourArea(contour) / max(1, area)
            if fill < 0.45:
                continue
            center_x = x1 + bx + bw // 2
            center_y = y1 + by + bh // 2
            # Prefer buttons around the vertical center of the game.
            score = area - abs(center_y - h * 0.55) * w * 0.15
            candidates.append((score, (center_x, center_y)))
        if not candidates:
            return None
        return max(candidates, key=lambda item: item[0])[1]

    def click_button_if_present(self, frame: np.ndarray) -> bool:
        point = self.find_start_button(frame)
        if point is None:
            return False
        assert self.window is not None
        print(f"[AUTO] دکمه رنگی احتمالی شروع/تکرار پیدا شد: {point}")
        pyautogui.click(self.window.left + point[0], self.window.top + point[1])
        # Keep the pointer out of the game so it cannot cover the character or branches.
        pyautogui.moveTo(0, 0, duration=0.08)
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
        start_candidate: tuple[int, int] | None = None
        start_streak = 0
        while not self.stop_requested:
            try:
                self.window = self.find_window()
            except RuntimeError:
                time.sleep(0.3)
                continue
            frame = self.capture()

            # Prioritize gameplay analysis. Only consider a start/replay button
            # after the player/tree could not be recognized for several frames.
            if self.analyze_and_play(frame):
                start_candidate = None
                start_streak = 0
                time.sleep(0.025)
                continue

            point = self.find_start_button(frame)
            if point is not None:
                if start_candidate is not None and abs(point[0] - start_candidate[0]) < 24 and abs(point[1] - start_candidate[1]) < 24:
                    start_streak += 1
                else:
                    start_candidate = point
                    start_streak = 1
                if start_streak >= 3 and self.click_button_if_present(frame):
                    start_candidate = None
                    start_streak = 0
                    continue
            else:
                start_candidate = None
                start_streak = 0
            time.sleep(0.05)
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
