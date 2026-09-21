$ports = @(8000, 3000)
$netstat = netstat -ano
foreach ($port in $ports) {
    foreach ($line in $netstat) {
        if ($line -match ":$port\s+.*LISTENING\s+(\d+)") {
            $pidToKill = [int]$matches[1]
            if ($pidToKill -gt 0) {
                try {
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                    Write-Host "Stopped process $pidToKill on port $port"
                } catch {}
            }
        }
    }
}
