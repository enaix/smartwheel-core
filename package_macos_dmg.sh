#!/bin/bash

if ! test -d "src/main.app/Contents"
then
    echo "Application binary not found. Starting the build..."
    ./build_macos.sh
fi

if ! hash create-dmg 2>/dev/null
then
    brew install create-dmg
fi

cd src

mv main.app smartwheel-core.app

create-dmg --volname "Smartwheel Core Installer" \
          --window-size 800 350 --icon "smartwheel-core.app" 100 100 \
          --app-drop-link 500 100 smartwheel-nightly.dmg \
          "smartwheel-core.app"