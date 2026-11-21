# LumberJackX

A small, console-based C practice game inspired by classic lumberjack games.

## Scope

LumberJackX is a standalone local practice project. It does not connect to Telegram, inspect another app's memory, automate a live game, or submit scores to online rooms or leaderboards.

## Build

### Windows (MinGW-w64)

```sh
gcc -std=c11 -Wall -Wextra -O2 src/main.c -o lumberjackx.exe
```

### Linux / macOS

```sh
cc -std=c11 -Wall -Wextra -O2 src/main.c -o lumberjackx
```

## Run

Windows: `./lumberjackx.exe`

Linux / macOS: `./lumberjackx`

## Controls

- `A`: move left
- `D`: move right
- `Q`: quit

## License

MIT. See [LICENSE](LICENSE).
