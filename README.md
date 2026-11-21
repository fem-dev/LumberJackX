# LumberJackX

Windows 10 x64 C++20 starter for a local, vision-assisted LumberJack game helper for Telegram Desktop.

## Current prototype
- Captures a user-selected desktop rectangle with Win32 GDI.
- Shows a preview with a small calibration toolbar.
- **ADD CIRCLE**: click this, then click the center of an on-screen game control in the preview.
- Select a marker by clicking its circle, then assign it with **LEFT** or **RIGHT**.
- **START / STOP** toggles the session state; the same button turns it off.
- Press **Q** or **Esc** to exit.

Markers are calibration points for the on-screen left/right controls. They are not branch detection zones. The automatic branch detector is still a safe placeholder, so START currently changes the session state and displays status but does not play or send clicks yet. This prevents accidental moves until the next milestone implements and tests branch recognition.

## Requirements
- Windows 10 x64
- Visual Studio 2022 (Desktop development with C++)
- CMake 3.20+
- OpenCV 4.x with CMake package configuration

## Build
```powershell
cmake -S . -B build -A x64 -DOpenCV_DIR="C:/opencv/build"
cmake --build build --config Release
```
Set `OpenCV_DIR` to the folder containing `OpenCVConfig.cmake`.

## Run
```powershell
.\build\Release\LumberJackX.exe --x 100 --y 100 --width 400 --height 600 --seconds 3600
```
The rectangle must cover the LumberJack mini app inside Telegram Desktop. The preview toolbar is added by the program.

## Controls
- Add circle: toolbar button or `A`, then click a game control in the preview.
- Select a circle: click it.
- Assign Left: toolbar button or `L`.
- Assign Right: toolbar button or `R`.
- Start/Stop: toolbar button or `S`.
- Exit: `Q` or `Esc`.

## Safety and scope
The project uses local screen capture and ordinary desktop interaction only. It does not inspect or modify Telegram/game servers, accounts, rooms, or scores. Use it in accordance with the game's rules.
