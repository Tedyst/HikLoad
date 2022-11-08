#!/bin/bash

python -m PyQt5.uic.pyuic -x MainWindow.ui -o MainWindow.py
python -m PyQt5.uic.pyuic -x Startup.ui -o Startup.py