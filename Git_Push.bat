@echo off
TITLE Github Quick-push


set /p commit_title="Enter Commit title (pushes with you as author): "


git add *
git commit -m "%commit_title%"
git pull 
git push


