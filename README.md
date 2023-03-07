![smartwheel-core](/extra/render1.jpg)

# Smartwheel Core

A powerful keyboard knob controller with GUI

![smartwheel-core ui](/extra/banner.png)

## Why do I need it?

The main problem with keyboard encoders and standalone dials is that there aren't many features out of the box, but *they can be much, much more powerful than they are right now*. Have you seen those techy gadgets from Hollywood blockbusters that hackers use (like Q's fancy joystick from latest 007)? Smartwheel gives you the same functionality, but adapted for day-to-day use.

Smartwheel is written in Python/PyQt6, so it could be easily modded with custom plugins. There aren't many right now, but this project is in constant development - there will be more soon.

## Features

#### Universal keyboards/dials support

Smartwheel will work with any knob - no support from the vendor required

#### A wide range of addons

There will be a wide range of plugins: from Krita/PS integrations to small quality-of-life imporvements

#### Theming

Smartwheel is fully customizable (you can even create any keybinds if you want)

## Installation

#### Development build

`git clone https://github.com/enaix/smartwheel-core.git`

`cd smartwheel-core`

Make sure that Python 3 is installed

`pip3 install -r requirements.txt`

`chmod +x ./launch.sh`

`./launch.sh`

## We need your help!

I've started working on this project a while ago, but it turned out that it's too big: it won't be possible to finish it without your help. However, it's much easier to implement features one-by-one: you only need basic Python3 (and sometimes PyQt6) knowledge. If you believe in this project and want to contribute, please DM me. Even small fixes, ideas or suggestions are very important.

## Documentation

Docs are available at readthedocs: https://smartwheel-core.readthedocs.io/en/latest/

## Release 0.0.1

- [x] Stable version (Linux)
- [x] Documentation (in progress)
- [ ] Examples (in progress)
- [x] Initial encoders support (Linux)
- [ ] Refactor api
  - [ ] Add modules asyncio background processes
  - [ ] Finish folders support
- [ ] Settings menu (in progress)
  - [X] Basic stuff
  - [X] Custom handlers support (Almost)
  - [X] Saving
  - [ ] Theme presets
  - [ ] Better overlays editor
  - [ ] Actions editor
  - [ ] Modules import (.zip)
- [ ] Add fancy blur
- [ ] Windows support (?)
- [ ] Mac support {?)

## Features progress

- [x] Base structure (Plugins manager)
- [x] Action engine
  - [x] Keyboard bindings
  - [ ] Serial encoder integration (Partial)
  - [ ] UX Features (acceleration)
  - [x] Keyboard knobs support (Almost)
- [ ] Settings editor (Partial)
- [ ] Custom plugins (from JSON)
- [x] Folders support (Partial)
- [x] Wheel UI
- [ ] Addons
  - [x] Media
  - [x] Color picker
  - [ ] Scroll
  - [ ] Files (Initial)
  - [ ] Rotate
  - [ ] Timeline
  - [ ] Other ...
- [x] Krita integration (Partial)
  - [x] Color
  - [ ] Canvas rotate/scale
  - [ ] Brush
  - [ ] ...
- [ ] Photoshop integration (?)

## DIY knob

If you don't have a standalone dial, you may 3D print one: there is a Freecad model in `pad` folder. Sadly, some components don't fit, but I don't have time to fix it right now. DM me if you need the fixed case model.

Upd: going to properly remodel it in F360 in the future

## Gallery

Short video (sorry for the poor quality): ![smartwheel.mp4](https://github.com/enaix/smartwheel-core/raw/master/extra/smartwheel.mp4)

Update: added UI overlays ![smartwheel2.mp4](https://github.com/enaix/smartwheel-core/raw/master/extra/simplescreenrecorder-2022-10-10_12.54.42.mp4)
