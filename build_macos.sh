#!/bin/bash
set -e

pip3 install nuitka

cp entrypoint.py src/main.py

cd src

python -m nuitka --standalone --assume-yes-for-downloads --disable-console --macos-create-app-bundle --macos-app-icon=smartwheel/logo.icns --macos-app-name="smartwheel-core" --macos-app-mode=ui-element --include-package=smartwheel --include-package=smartwheel.actions --include-package=smartwheel.backgrounds --include-package=smartwheel.serialpipe --include-package=smartwheel.settings_handlers --include-package=smartwheel.ui --include-package=smartwheel.ui.internal --enable-plugin=pyqt6 --include-data-dir=PyQt6=PyQt6 --include-data-dir=./smartwheel=smartwheel ./main.py
