@echo off
set HERE=%~dp0
cd /d "%HERE%"
python client.py examples\batch_all.json work\resp_batch.json
echo CLIENT_EXIT=%ERRORLEVEL%
