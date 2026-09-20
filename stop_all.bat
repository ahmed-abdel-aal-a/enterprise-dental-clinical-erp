@echo off
echo ==========================================================
echo [DentApex Enterprise] Stopping servers on 8000 and 3000...
echo ==========================================================
powershell -NoProfile -Command "& { 8000, 3000 | ForEach-Object { $p = $_; Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } } }"
echo [DentApex Enterprise] Ports 8000 and 3000 cleared successfully!
echo ==========================================================
