# LumberJackX

Automatic screen-based player for the **LumberJack Telegram Mini App** on Windows.

## What it does

- Finds the Telegram window by its title (no manually entered screen coordinates).
- Captures that window and analyzes the game image.
- Looks for Play/Start/Replay/Again text with OCR and clicks the detected button.
- Uses image processing to estimate the tree, player side, and branch position.
- Sends Left/Right key presses automatically.

The visual detector is heuristic and has **not yet been validated against every Telegram Mini App theme or scaling setting**. If it does not recognize your game correctly, stop it with Esc and share a screenshot of the game window so the detector can be tuned to the exact Mini App appearance.

## Windows setup

1. Install Python 3.11 or newer.
2. Install the Tesseract OCR application and make sure `tesseract.exe` is on PATH.
   - The Python package alone is not enough; the OCR application is also required.
3. In PowerShell, from this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Open the LumberJack Mini App in Telegram Desktop before starting the script.

## Controls

- `Esc`: stop the bot.
- `Ctrl+C`: stop from the terminal.

Keep the Telegram game window visible and unminimized while it runs. Do not interact with other windows during play.

## Detection notes

This version combines ideas commonly used by public LumberJack bots: fast screen capture, color/region analysis, and queued keyboard input. It does not copy their source files. Unlike coordinate-based examples, it locates the Telegram window at runtime and derives image coordinates from the current window bounds.

Because Telegram Mini App rendering can differ from the older tbot.xyz/browser game, the detector should be tested on the exact Mini App before relying on it for a full run.
