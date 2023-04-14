![smartwheel-core](/extra/render1.jpg)

![smartwheel-core logo](/extra/logo.png)

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

You may install the prebuilt stable version from the releases.

#### Development build

Make sure that Python 3 is installed

#### Stable version

`pip3 install smartwheel-core`

#### From Github

`git clone https://github.com/enaix/smartwheel-core.git`

`cd smartwheel-core`

`pip3 install .`

#### Compilation

Nuitka now supports only Python <= 3.10

`./build.sh` or `.\build.bat`

## We need your help!

I've started working on this project a while ago, but it turned out that it's too big: it won't be possible to finish it without your help. However, it's much easier to implement features one-by-one: you only need basic Python3 (and sometimes PyQt6) knowledge. If you believe in this project and want to contribute, please DM me. Even small fixes, ideas or suggestions are very important.

## Documentation

Docs are available at readthedocs: https://smartwheel-core.readthedocs.io/en/latest/

## Release 0.1.0

- [x] Stable version (Linux)
- [x] Documentation (in progress)
- [ ] Examples (in progress)
- [x] Initial encoders support (Linux)
- [ ] Refactor api
  - [X] Move to PyQt6
  - [X] Add colorable icons
  - [X] Add modules background processes
  - [ ] Rewrite serial input with new api
  - [ ] Add media fetching on Windows
  - [ ] Add key combos
  - [ ] Finish folders support
- [ ] Settings menu (in progress)
  - [X] Basic stuff
  - [X] Custom handlers support (Almost)
  - [X] Saving
  - [X] Theme presets
  - [X] Add color picker
  - [X] Actions editor
  - [ ] Sections editor
  - [ ] Add unified input editor (new input api)
  - [ ] Better overlays editor (?)
  - [ ] Modules import (.zip) (?)
- [ ] Wheel hiding
  - [ ] Hide after timeout
  - [ ] Hide after losing window focus
- [ ] Packaging
  - [X] Configure setup.py
  - [ ] Add auto update feature
  - [ ] Hire core doctor!
- [ ] Windows support
  - [ ] (Platform) Replace AF_UNIX socket with network socket
- [ ] Add fancy blur (?)
- [ ] Mac support (?)

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
  - [ ] MIDI device (with multiple encoders)
  - [ ] Other ...
- [x] Krita integration (Partial)
  - [x] Color
  - [ ] Canvas rotate/scale
  - [ ] Brush
  - [ ] ...
- [ ] Photoshop integration (?)

## DIY knob

If you don't have a standalone dial, you may 3D print one! 

### [smartwheel pad](https://github.com/enaix/smartwheel-pad-mk1)

## Gallery

Short video (sorry for the poor quality): ![smartwheel.mp4](https://github.com/enaix/smartwheel-core/raw/master/extra/smartwheel.mp4)

Update: added UI overlays ![smartwheel2.mp4](https://github.com/enaix/smartwheel-core/raw/master/extra/simplescreenrecorder-2022-10-10_12.54.42.mp4)

## Resources

Ionicons icon set https://github.com/ionic-team/ionicons
