# LumberJackX

Automatic screen-based player for the **LumberJack Telegram Mini App** on Windows.

## What it does

- Finds the Telegram window by its title (no manually entered screen coordinates).
- Captures that window and analyzes the game image.
- Looks for a prominent colored start/replay button using OpenCV (no OCR, external OCR app, or image template files).
- Uses image processing to estimate the tree, player side, and branch position.
- Sends Left/Right key presses automatically.

The visual detector is heuristic and has **not yet been validated against every Telegram Mini App theme or scaling setting**. In particular, automatic start/replay button detection relies on button color and shape. If it does not recognize your game correctly, stop it with Esc and share a screenshot of the game window so the detector can be tuned to the exact Mini App appearance.

## Windows setup (Git clone)

1. Install Python 3.11 or newer and Git.
2. Open PowerShell and run:

```powershell
git clone https://github.com/fem-dev/LumberJackX.git
cd LumberJackX
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Open the LumberJack Mini App in Telegram Desktop before starting the script. No EXE download and no Tesseract/OCR installation are required.

If PowerShell blocks virtual-environment activation, run this once in that PowerShell window, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Update later

From inside the cloned project folder:

```powershell
git pull
python -m pip install -r requirements.txt
python main.py
```

## Controls

- `Esc`: stop the bot.
- `Ctrl+C`: stop from the terminal.

Keep the Telegram game window visible and unminimized while it runs. Do not interact with other windows during play.

## Detection notes

This version combines fast screen capture, color/region analysis, and keyboard input. It does not copy other projects' source files. Unlike coordinate-based examples, it locates the Telegram window at runtime and derives image coordinates from the current window bounds.

Because Telegram Mini App rendering can differ from older browser versions of the game, the detector should be tested on the exact Mini App before relying on it for a full run.
