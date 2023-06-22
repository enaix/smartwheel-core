#!/bin/bash
set -e

pip3 install nuitka

cp entrypoint.py src/main.py

cd src

python -m nuitka --standalone --disable-console --macos-create-app-bundle --macos-app-icon=smartwheel/logo.icns --macos-app-name="smartwheel-core" --macos-app-mode=ui-element --include-module=smartwheel --include-module=smartwheel.actions --include-module=smartwheel.backgrounds --include-module=smartwheel.serialpipe --include-module=smartwheel.settings_handlers --include-module=smartwheel.ui --include-module=smartwheel.ui.internal --enable-plugin=pyqt6 --include-data-dir=PyQt6=PyQt6 --include-data-dir=./smartwheel=smartwheel ./main.py
