@echo off
set HERE=%~dp0
cd /d "%HERE%"
if exist make_template.log del make_template.log
CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 4" --runscript="%HERE%make_template.py" --noUI 1>make_template_console.log 2>&1
echo EXIT=%ERRORLEVEL%
