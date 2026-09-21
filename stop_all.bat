@echo off
echo ==========================================================
echo [DentApex Enterprise] Stopping servers on 8000 and 3000...
echo ==========================================================

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_ports.ps1"

echo [DentApex Enterprise] Ports 8000 and 3000 cleared successfully!
echo ==========================================================
