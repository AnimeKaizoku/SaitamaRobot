@echo off
SLEEP 5
py -3.6 --version
IF "%ERRORLEVEL%" == "0" (
    py -3.6 -m tg_bot
) ELSE (
    py -m tg_bot
)
pause