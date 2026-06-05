@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%src"

set "BUNDLED_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PYTHON%" (
  set "PYTHON=%BUNDLED_PYTHON%"
) else (
  set "PYTHON=python"
)

set "COMMAND=%~1"
if /I "%COMMAND%"=="review" goto run_with_ai
if /I "%COMMAND%"=="review-pr" goto run_with_ai
if /I "%COMMAND%"=="github" goto run_with_ai
if /I "%COMMAND%"=="paranoid" goto run_with_ai
if /I "%COMMAND%"=="architecture" goto run_with_ai
if /I "%COMMAND%"=="doctor" goto run_with_ai
if /I "%COMMAND%"=="ui" goto run_with_ai

"%PYTHON%" -m tripwire %*
exit /b %ERRORLEVEL%

:run_with_ai
"%PYTHON%" -m tripwire %* --provider ollama --model qwen3:8b
exit /b %ERRORLEVEL%
