---
title: "Games"
summary: "Visual novels and small games with jade-vn-engine: new, check and build from the CLI, MCP or HTTP."
tags: [vn, games, webxdc, micropython, renpy]
applies_to: stack
audience: both
since: 0.1.0
order: 12
---
# Games

[jade-vn-engine](https://github.com/lucky-edgelord/jade-vn-engine) plays scripts written in a subset of Ren'Py's script language. The Python parts of a script run on MicroPython in the browser.

A game is a folder:

- `game.toml` holds the name, the icon and the engine libraries the game uses (`libs = "rpg, minigames"`).
- One or more `*.rpy` scripts.
- An `assets/` folder.

The toolkit builds a game with the engine's own compiler and packager, at the commit pinned in `STACK.md`. That commit is downloaded once into `~/.cache/jade`. Set `JADE_VN_ENGINE`, or pass `--engine`, to use a local checkout instead.

## Commands

| Command | Does |
| --- | --- |
| `jade vn new NAME [--libs rpg,minigames]` | writes `NAME/game.toml`, `NAME/script.rpy` and `NAME/assets/` |
| `jade vn check DIR` | compiles the scripts and returns the labels, or a JADE407 error that names the file and line |
| `jade vn build DIR [--cdn] [--out DIR]` | writes a playable folder and `dist/NAME.xdc` |

By default the build bundles the engine, so the `.xdc` works offline. With `--cdn` it loads the engine from the pinned CDN path instead, which makes the game a few kB plus its assets.

Over MCP the tools are `vn_new`, `vn_check` and `vn_build`. Over HTTP use `POST /v1/commands/vn.build` with the same arguments.

## See it

The three commands, run for real:

![jade vn new, check and build](https://lucky-edgelord.github.io/jade-agent-stack/img/term-vn.webp)

The starter game that `jade vn new` writes, running (the title screen, a line, a choice):

![The starter game's title screen](https://lucky-edgelord.github.io/jade-agent-stack/img/game-start.webp)
![The starter game: a line of dialogue](https://lucky-edgelord.github.io/jade-agent-stack/img/game-say.webp)
![The starter game: a choice](https://lucky-edgelord.github.io/jade-agent-stack/img/game-menu.webp)

## What the engine does

- **Script:** labels, menus, `$` Python, ATL transforms, screens, rollback, saves and audio channels.
- **Effects:** post effects such as CRT, VHS, Vectoria scanlines and colour LUTs, Loci-style lighting, and analog tape noise.
- **Modes:** a tile scroller and map, turn-based battles (`libs = "rpg"`), faux-3D tours of photographed interiors, minigames (`libs = "minigames"`) and Live2D.

Each part loads lazily, the first time a game uses it. See the engine's README for the script reference.

## Errors

- **JADE407:** a script did not compile. The message names the file and the line.
- **JADE409:** the engine checkout is missing. Check that the path points to a jade-vn-engine checkout.
- **JADE200:** the download failed. You are offline: set `JADE_VN_ENGINE`.

## Modes in motion

These GIFs come from the engine's sample games (see its [gallery](https://github.com/lucky-edgelord/jade-vn-engine#gallery)).

![A tile scroller: walking](https://lucky-edgelord.github.io/jade-agent-stack/img/rpg-walk.gif)
![A turn-based battle](https://lucky-edgelord.github.io/jade-agent-stack/img/rpg-battle.gif)
![A faux-3D tour: dragging to look around](https://lucky-edgelord.github.io/jade-agent-stack/img/tour-look.gif)
![Lighting levels in Jade's Vault](https://lucky-edgelord.github.io/jade-agent-stack/img/vault-lights.gif)
![Jade in Live2D, the same model as in Jade Vault](https://lucky-edgelord.github.io/jade-agent-stack/img/live2d.jpg)
