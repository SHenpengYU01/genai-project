@echo off
rem Usage: run_compile.bat <absolute request.json> <absolute response.json>
set TOOLDIR=%~dp0
cd /d "%TOOLDIR%"
if not exist work mkdir work
if exist "%~2" del "%~2"
CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 4" --runscript="%TOOLDIR%compile_worker.py" --scriptargs:'%~1 %~2' --noUI 1>compile_console.log 2>&1
echo EXIT=%ERRORLEVEL%
