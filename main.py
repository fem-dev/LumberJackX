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
from pynput.mouse import Listener as MouseListener


WINDOW_PATTERN = re.compile(r"lumber\\s*jack", re.IGNORECASE)
STOP_KEY = Key.esc
ACTION_INTERVAL = 0.16
PATCH_RADIUS = 5
DARK_PIXEL_THRESHOLD = 200
BRANCH_PIXEL_RATIO = 0.22


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
        self.points: dict[str, tuple[int, int]] = {}
        self.direction = "left"
        self.last_action = 0.0
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

    def capture_click(self, instruction: str) -> tuple[int, int]:
        assert self.window is not None
        if self.stop_requested:
            raise KeyboardInterrupt
        print(instruction, flush=True)
        result: list[tuple[int, int]] = []

        def on_click(x, y, button, pressed):
            if pressed:
                result.append((int(x), int(y)))
                return False

        with MouseListener(on_click=on_click) as mouse_listener:
            while mouse_listener.is_alive() and not self.stop_requested:
                time.sleep(0.05)
        if self.stop_requested or not result:
            raise KeyboardInterrupt
        x, y = result[0]
        # Park the cursor outside the game immediately after calibration.
        pyautogui.moveTo(0, 0, duration=0.08)
        rel_x, rel_y = x - self.window.left, y - self.window.top
        if not (0 <= rel_x < self.window.width and 0 <= rel_y < self.window.height):
            raise RuntimeError("نقطه انتخاب‌شده خارج از پنجره بازی بود؛ دوباره اجرا کن.")
        return rel_x, rel_y

    def calibrate(self) -> None:
        print("\n[SETUP] نشانگر موس را روی محل برخورد شاخه با سر بازیکن در سمت چپ ببر و یک بار کلیک کن.")
        self.points["left"] = self.capture_click("[WAIT] کلیک نقطه سمت چپ...")
        print("[OK] نقطه چپ ثبت شد.")
        print("[SETUP] حالا محل متناظر در سمت راست را یک بار کلیک کن.")
        self.points["right"] = self.capture_click("[WAIT] کلیک نقطه سمت راست...")
        print("[OK] هر دو نقطه ثبت شدند؛ موس به گوشه صفحه منتقل شد.")
        print("[TIP] این دو نقطه باید هم‌ارتفاع با محل سر بازیکن و جایی باشند که شاخه از آن عبور می‌کند.")

    def branch_detected(self, frame: np.ndarray, side: str) -> bool:
        x, y = self.points[side]
        r = PATCH_RADIUS
        patch = frame[max(0, y-r):min(frame.shape[0], y+r+1),
                      max(0, x-r):min(frame.shape[1], x+r+1)]
        if patch.size == 0:
            return False
        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        dark_ratio = float(np.mean(gray < DARK_PIXEL_THRESHOLD))
        return dark_ratio >= BRANCH_PIXEL_RATIO

    def press(self, side: str) -> None:
        key = Key.left if side == "left" else Key.right
        self.keyboard.press(key)
        self.keyboard.release(key)
        self.direction = side
        self.last_action = time.monotonic()

    def run(self) -> None:
        self.window = self.find_window()
        print(f"[OK] پنجره پیدا شد: {self.window.title} ({self.window.width}x{self.window.height})")
        self.calibrate()
        print(f"[INFO] سرعت حرکت: هر {ACTION_INTERVAL:.2f} ثانیه؛ توقف با Esc.")
        print("[INFO] بازی را در صفحه نگه دار؛ بات وضعیت دو نقطه را بررسی می‌کند.")
        while not self.stop_requested:
            try:
                self.window = self.find_window()
            except RuntimeError:
                time.sleep(0.3)
                continue
            frame = self.capture()

            blocked = self.branch_detected(frame, self.direction)
            next_side = ("right" if self.direction == "left" else "left") if blocked else self.direction
            if time.monotonic() - self.last_action >= ACTION_INTERVAL:
                self.press(next_side)
            time.sleep(0.025)

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
        print("\n[STOP] توقف شد.")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    finally:
        bot.close()


if __name__ == "__main__":
    raise SystemExit(main())
