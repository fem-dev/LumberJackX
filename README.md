# LumberJackX

Windows 10 C++20 starter for a local, vision-assisted LumberJack game player.

## Scope
- Captures a user-selected desktop region using Win32 GDI.
- Uses OpenCV as the image-processing foundation.
- Sends ordinary Left/Right keyboard input through Win32 `SendInput` when a calibrated detector is ready.
- Tracks a configurable session timer.
- Does not inspect or modify Telegram/game servers, accounts, scores, or room state.

## Requirements
- Windows 10 x64
- Visual Studio 2022 (Desktop development with C++)
- CMake 3.20+
- OpenCV 4.x with CMake package configuration

## Build
`cmake -S . -B build -A x64 -DOpenCV_DIR="C:/opencv/build"`
`cmake --build build --config Release`

Adjust `OpenCV_DIR` to the directory containing `OpenCVConfig.cmake`.

## Run
`build\\Release\\LumberJackX.exe --x 100 --y 100 --width 400 --height 600 --seconds 60`

The first milestone is verifying the capture preview. Branch detection deliberately returns Unknown until calibrated with representative screenshots, so the starter does not send gameplay inputs by default.

## Layout
- `include/`: public interfaces
- `src/`: Win32 capture/input, timer, detector and decision engine
- `tests/`: reserved for detector tests

Use only normal visible keyboard input and respect the game's rules.