@echo off
chcp 65001 > nul
echo ===================================================
echo   DANG PUSH CODE LEN GITHUB: App-c-u-chuy-n
echo ===================================================
cd /d "d:\APP AI"

"C:\Program Files\Git\cmd\git.exe" add .
"C:\Program Files\Git\cmd\git.exe" commit -m "Update and configure for Vercel deployment"
"C:\Program Files\Git\cmd\git.exe" push origin main

echo.
echo ===================================================
echo COMPLETED / HOAN THANH!
echo ===================================================
pause
