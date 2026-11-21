# LumberJackX

**Version 0.2.0 — Windows 10 x64 / C++20**

A local desktop prototype for the Telegram Desktop LumberJack mini app. It uses Win32 desktop capture and OpenCV for the preview and calibration UI.

## Implemented in v0.2
- Win32 GDI screen capture with correct bitmap deselection before GetDIBits.
- Live OpenCV preview with an overlay toolbar.
- Add a circle by choosing ADD CIRCLE and clicking the corresponding game-control position in the preview.
- Select a circle and label it LEFT or RIGHT. Unlabelled circles are shown in yellow.
- Prevent START until both LEFT and RIGHT controls have been defined.
- One START / STOP button, plus keyboard shortcuts.
- Session timer that starts on START and stops on STOP or timeout.
- Calibration is saved to lumberjackx.yml and restored on next launch.
- CTest coverage for decision mapping, safe unknown detection, and configuration round-trip.

## Important current limitation
The branch detector intentionally returns Unknown for every frame. This is a fail-safe placeholder, not a finished vision model. START currently runs the session timer and status display; it does not make game moves or send mouse clicks. The next milestone is to calibrate branch recognition against real gameplay screenshots at the exact game resolution and phase. We should not enable automatic input until detection has been validated on varied frames.

The LEFT/RIGHT circles mark the on-screen game controls. They are not branch-sensor regions.

## Requirements
- Windows 10 x64
- Visual Studio 2022 with Desktop development with C++
- CMake 3.20+
- OpenCV 4.x (C++ development package and CMake config)

## Build
Open Developer PowerShell:

```powershell
cmake -S . -B build -A x64 -DOpenCV_DIR="C:/opencv/build"
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

Set OpenCV_DIR to the directory that contains OpenCVConfig.cmake.

## Run
Example for a 400x700 game window whose top-left desktop position is (100, 100):

```powershell
.\build\Release\LumberJackX.exe --x 100 --y 100 --width 400 --height 700 --seconds 3600
```

Adjust the capture rectangle to cover the LumberJack mini app in Telegram Desktop. The preview adds its own toolbar above the captured image. The rectangle and marker calibration are stored in lumberjackx.yml.

## Controls
- ADD CIRCLE or A: enter marker-placement mode, then click the desired control position in the game preview.
- Click an existing circle: select it.
- LEFT or L: label the selected circle as the left game control.
- RIGHT or R: label the selected circle as the right game control.
- START / STOP or S: toggle the session.
- SAVE: write the current calibration.
- Q or Esc: exit.

## Project layout
- include/: public interfaces and configuration types
- src/: screen capture, calibration persistence, detector, decision engine, timer and controller
- tests/: basic unit tests

## Scope
All current image processing is local. The project does not inspect or modify Telegram/game servers, accounts, rooms, or score data. Use it in accordance with the game's rules.
