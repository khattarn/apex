@echo off
cd /d "c:\Projects\apex\dialpad-app"
rem VS Code sets this, and with it set Electron starts as plain Node and the app crashes on launch.
set ELECTRON_RUN_AS_NODE=
npm start
