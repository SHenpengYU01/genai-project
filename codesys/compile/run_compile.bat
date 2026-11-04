@echo off
rem Usage: run_compile.bat <absolute request.json> <absolute response.json>
set HERE=%~dp0
cd /d "%HERE%"
if not exist work mkdir work
if exist "%~2" del "%~2"
CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 4" --runscript="%HERE%worker.py" --scriptargs:'%~1 %~2' --noUI 1>compile_console.log 2>&1
echo EXIT=%ERRORLEVEL%
