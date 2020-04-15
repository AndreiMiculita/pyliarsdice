## Liar's Dice implemented in python

First run `pip install -r requirements.txt`.
Then run main.py.

If the application doesn't respect the system theme and it bothers you:
* `pip uninstall PySide2`
* [try this guide to build from source](https://doc.qt.io/qtforpython/gettingstarted.html#guides-per-platform).

If app doesn't stop with Stop button (Ctrl+F2) in PyCharm, you can still close with Ctrl+W or close button from inside the app, or set environment variable `PYDEVD_PYQT_MODE` to `pyside`. This should also fix debugging breakpoints not working.