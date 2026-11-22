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

Open the LumberJack Mini App in Telegram Desktop before running the bot. Keep the game window visible and do not minimize it.

The bot now attempts to:
1. Find the game window automatically.
2. Detect the large Play or Retry button and click it automatically.
3. Detect the red-shirt player and the nearest green branch.
4. Press the direction away from the nearest branch.

No manual calibration clicks, EXE file, OCR, or Tesseract are required. Press `Esc` to stop the bot. The mouse is moved to the screen corner after an automatic Play/Retry click.

## Detection notes

The automatic detector uses OpenCV color masks and connected components based on the supplied game screenshots:
- Green shapes above the grass platform are treated as branches.
- The lowest visible branch is treated as the nearest branch.
- The red player sprite is used to confirm that the gameplay screen is active.
- A single orange/brown circular button near the lower center is treated as Play or Retry.

The detector has not yet been validated across different Telegram window sizes, display scaling settings, animations, or game versions. If it does not detect the game correctly, send a screenshot of the game window and the terminal output.

The default action interval is `0.16` seconds. To change it, edit `ACTION_INTERVAL` near the top of `main.py`.

If PowerShell does not allow environment activation, run this command in the same window, then try activation again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
