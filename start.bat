@echo off
TITLE Saitama Robot
py -3.7 --version
IF "%ERRORLEVEL%" == "0" (
    py -3.7 -m tg_bot
) ELSE (
    py -m tg_bot
)

pause