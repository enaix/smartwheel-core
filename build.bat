pip install nuitka

copy entrypoint.py src\main.py

cd src

python -c "while True: print('Yes')" | python -m nuitka --standalone --disable-console --follow-imports --include-module=smartwheel.actions --include-module=smartwheel.backgrounds --include-module=smartwheel.serialpipe --include-module=smartwheel.settings_handlers --include-module=smartwheel.ui --include-module=smartwheel.ui.internal --enable-plugin=pyqt6 --include-data-dir=.\smartwheel=smartwheel --disable-console .\main.py
