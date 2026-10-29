@echo off
cd /d "%~dp0"
python codesys_build.py examples\batch_all.json work\resp_batch.json
echo CLIENT_EXIT=%ERRORLEVEL%
