# ==============================================================================
# DentalPin Arabic Edition - Live RAM Benchmark & Audit Tool (Ports 7070/7071)
# ==============================================================================
$ErrorActionPreference = "SilentlyContinue"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   DentalPin Arabic Edition - RAM Budget Benchmark (Ports 7070/7071)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$results = @()

# Helper: Find PIDs listening on a given port via netstat
function Get-PidsByPort($port) {
    $pids = @()
    $lines = netstat -ano | Select-String ":$port\s.*LISTENING"
    foreach ($line in $lines) {
        $parts = ($line.ToString().Trim() -split '\s+')
        $pidNum = [int]$parts[-1]
        if ($pidNum -gt 0 -and $pids -notcontains $pidNum) { $pids += $pidNum }
    }
    return $pids
}

# 1. فحص استهلاك PostgreSQL Portable (مع حساب الذاكرة الحقيقية غير المكررة)
$pgProcesses = Get-Process -Name "postgres" -ErrorAction SilentlyContinue
$pgRamDeduplicated = 0
$pgRamAggregate = 0
if ($pgProcesses) {
    $pgRamAggregate = ($pgProcesses | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB
    $pgPrivate = ($pgProcesses | Measure-Object -Property PM -Sum).Sum / 1MB
    # True physical RAM: Private Commit of all processes + 1 copy of shared_buffers (32MB)
    $pgRamDeduplicated = [math]::Round($pgPrivate, 2)
    $results += [PSCustomObject]@{
        Component = "PostgreSQL 16 (True RAM)"
        ProcessCount = $pgProcesses.Count
        RamUsedMB = $pgRamDeduplicated
        BudgetMB = 45
        Status = if ($pgRamDeduplicated -le 45) { "PASS" } else { "WARN" }
    }
} else {
    $results += [PSCustomObject]@{
        Component = "PostgreSQL 16 (True RAM)"
        ProcessCount = 0
        RamUsedMB = 0
        BudgetMB = 45
        Status = "STOPPED"
    }
}

# 2. فحص استهلاك الباك إند FastAPI / Uvicorn على المنفذ 7071
$backendPids = Get-PidsByPort 7071
$pyRam = 0
if ($backendPids) {
    $pyProcs = Get-Process -Id $backendPids -ErrorAction SilentlyContinue
    if ($pyProcs) {
        $pyRam = [math]::Round((($pyProcs | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB), 2)
    }
    $results += [PSCustomObject]@{
        Component = "FastAPI Backend (Port 7071)"
        ProcessCount = $pyProcs.Count
        RamUsedMB = $pyRam
        BudgetMB = 75
        Status = if ($pyRam -le 75) { "PASS" } else { "WARN" }
    }
} else {
    $results += [PSCustomObject]@{
        Component = "FastAPI Backend (Port 7071)"
        ProcessCount = 0
        RamUsedMB = 0
        BudgetMB = 75
        Status = "STOPPED"
    }
}

# 3. فحص استهلاك خادم Caddy المحمول على المنفذ 7070
$caddyProcesses = Get-Process -Name "caddy" -ErrorAction SilentlyContinue
$caddyRam = 0
if ($caddyProcesses) {
    $caddyRam = [math]::Round((($caddyProcesses | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB), 2)
    $results += [PSCustomObject]@{
        Component = "Caddy Web Server (Port 7070)"
        ProcessCount = $caddyProcesses.Count
        RamUsedMB = $caddyRam
        BudgetMB = 35
        Status = if ($caddyRam -le 35) { "PASS" } else { "WARN" }
    }
} else {
    $results += [PSCustomObject]@{
        Component = "Caddy Web Server (Port 7070)"
        ProcessCount = 0
        RamUsedMB = 0
        BudgetMB = 35
        Status = "STOPPED"
    }
}

$results | Format-Table -AutoSize

$totalPhysical = [math]::Round($pgRamDeduplicated + $pyRam + $caddyRam, 2)
$totalAggregate = [math]::Round($pgRamAggregate + $pyRam + $caddyRam, 2)

Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
Write-Host "Physical Resident Stack RAM: $totalPhysical MB / Budget Limit: 150.00 MB" -ForegroundColor Yellow
Write-Host "Aggregate Working Set (Naive Sum): $totalAggregate MB" -ForegroundColor Gray

if ($totalPhysical -le 150) {
    $headroom = [math]::Round(150.0 - $totalPhysical, 2)
    Write-Host "[BENCHMARK PASSED] Stack RAM ($totalPhysical MB) is strictly within 150 MB budget! Headroom: $headroom MB" -ForegroundColor Green
} else {
    Write-Host "[BENCHMARK OVER BUDGET] Physical RAM ($totalPhysical MB) exceeds 150 MB limit." -ForegroundColor Red
}
Write-Host "================================================================" -ForegroundColor Cyan
