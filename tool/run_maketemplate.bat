@echo off
set TOOLDIR=%~dp0
cd /d "%TOOLDIR%"
if exist make_template.log del make_template.log
CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 4" --runscript="%TOOLDIR%make_template.py" --noUI 1>make_template_console.log 2>&1
echo EXIT=%ERRORLEVEL%
