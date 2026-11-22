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

The bot now uses a pretrained-library reinforcement-learning implementation (Stable-Baselines3 DQN) and attempts to:
1. Find the game window automatically.
2. Detect the large Play or Retry button and click it automatically.
3. Detect the red-shirt player and the nearest green branch.
4. Feed the detected player/branch state to a DQN agent and press its selected direction.
5. Reward each detected surviving move with +1 chocolate and each detected death with -5 chocolates.

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


## DQN learning model

The decision-making model uses **Stable-Baselines3 DQN** with a Gymnasium environment adapter. It is not a hand-written Q-table: the neural-network policy and experience replay are provided by the library. The initial policy starts with exploration and receives the screen-derived player/branch state. Each detected surviving move earns +1 virtual chocolate; a detected death earns -5.

The model checkpoint is saved as `lumberjack_dqn.zip`, its replay buffer as `lumberjack_replay_buffer.pkl`, and reward events are appended to `training_log.jsonl`. These files are created beside `main.py` and reused on the next run.

The screen detector and reward signals are heuristic, so incorrect visual detections can teach the agent incorrect behavior. The first runs should be supervised. Stable-Baselines3 supplies the DQN algorithm; it does not include a pretrained LumberJack-specific policy.
