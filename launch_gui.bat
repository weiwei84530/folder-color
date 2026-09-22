@echo off
:: Launch FolderColor GUI without opening a command prompt window
chcp 65001 >nul
cd /d "%~dp0"
start "" pythonw.exe "%~dp0gui.py" %*
