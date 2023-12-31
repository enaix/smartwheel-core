pip install nuitka

copy entrypoint.py src\main.py

cd src

python -m nuitka --standalone --assume-yes-for-downloads --windows-icon-from-ico=smartwheel/logo.ico --follow-imports --include-package=smartwheel --include-package=smartwheel.actions --include-package=smartwheel.backgrounds --include-package=smartwheel.serialpipe --include-package=smartwheel.settings_handlers --include-package=smartwheel.ui --include-package=smartwheel.ui.internal --enable-plugin=pyqt6 --include-data-dir=.\smartwheel=smartwheel .\main.py
