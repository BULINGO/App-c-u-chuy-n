@echo off
chcp 65001 > nul
echo ===================================================
echo   DANG PUSH CODE LEN GITHUB: App-c-u-chuy-n
echo ===================================================
cd /d "d:\APP AI"

"C:\Program Files\Git\cmd\git.exe" remote set-url origin https://github.com/BULINGO/App-c-u-chuy-n.git
"C:\Program Files\Git\cmd\git.exe" push -u origin main

echo.
echo ===================================================
echo COMPLETED / HOAN THANH!
echo ===================================================
pause
