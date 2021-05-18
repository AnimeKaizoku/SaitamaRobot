@echo off
TITLE Github Quick-pushing

:: Print the branch cause people like me push to wrong branches and cry about it later.
echo Pushing to branch:
git branch
echo.
:: Take input for comment and thats about it
set /p commit_title="Enter Commit title (pushes with you as author): "

:: If you are reading comments to understand this part then you can go back stab yourself.
echo.
git pull
git add *
git commit -m "%commit_title%"
git push


:: Hail Hydra
