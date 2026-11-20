@echo off
setlocal
cd /d "%~dp0"
title Treasury Bridge

where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 goto try_python
py -3 "scripts\start_windows.py" %*
set "TB_EXIT=%errorlevel%"
goto finished

:try_python
where python >nul 2>nul
if errorlevel 1 goto missing_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 goto missing_python
python "scripts\start_windows.py" %*
set "TB_EXIT=%errorlevel%"
goto finished

:missing_python
echo.
echo Nao encontrei Python 3.11 ou superior neste computador.
echo Instale o Python pelo site oficial:
echo https://www.python.org/downloads/windows/
echo Depois feche esta janela e abra INICIAR_WINDOWS.bat novamente.
set "TB_EXIT=1"

:finished
if /i "%~1"=="--check" exit /b %TB_EXIT%
echo.
echo A ferramenta foi encerrada. Se houve um erro, a mensagem esta acima.
pause
exit /b %TB_EXIT%
