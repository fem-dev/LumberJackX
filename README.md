# LumberJackX

Automatic screen-based player for the **LumberJack Telegram Mini App** on Windows.

## Run on Windows

Python 3.11+ and Git must be installed. Open PowerShell and run:

```powershell
git clone https://github.com/fem-dev/LumberJackX.git
cd LumberJackX
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Before starting the bot, open the game in Telegram Desktop and enter the game screen. When the bot starts:

1. When prompted, click the LEFT detection point, level with the player's head. Choose the spot where a branch passes as it approaches.
2. Click the matching detection point on the RIGHT side.
3. After both points are saved, the cursor moves to the screen corner and the bot starts playing.

Press `Esc` to stop the bot. If the game ends, restart the game manually. The calibration points remain saved until you close the program.

No EXE file, OCR, or Tesseract is required. For later runs, activate the virtual environment inside the project folder and run `python main.py`. To get the latest changes, run `git pull` first.

## Detection method

- At startup, two fixed points where branches pass are calibrated.
- In each frame, the bot checks a small area around the point on the current side instead of trying to identify the player's clothing color or locate the trunk.
- If the proportion of dark pixels in that area exceeds the configured threshold, the bot changes direction.
- The default action interval is `0.16` seconds. Thresholds and patch size can be adjusted near the top of `main.py`.

This method is simpler to calibrate than the previous broad color-detection approach, but it still needs to be tested with the actual game window size and appearance. If the points are selected incorrectly, or the branch and background colors differ, the thresholds may need adjustment.

If PowerShell does not allow environment activation, run this command in the same window, then try activation again: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
