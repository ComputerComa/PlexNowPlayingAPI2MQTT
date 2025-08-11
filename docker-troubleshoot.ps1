# docker-troubleshoot.ps1 - Docker networking troubleshooting script for Windows

Write-Host "=== Docker Container Troubleshooting ===" -ForegroundColor Cyan
Write-Host

# Check if Docker is available
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check container status
Write-Host
Write-Host "📋 Container Status:" -ForegroundColor Yellow
try {
    docker ps -a --filter "name=plex-mqtt-bridge"
} catch {
    Write-Host "❌ Cannot check container status" -ForegroundColor Red
}

# Check container logs
Write-Host
Write-Host "📝 Recent Container Logs:" -ForegroundColor Yellow
try {
    docker logs --tail 20 plex-mqtt-bridge
} catch {
    Write-Host "❌ Container not found or not running" -ForegroundColor Red
}

# Check port mapping
Write-Host
Write-Host "🔌 Port Mapping:" -ForegroundColor Yellow
try {
    docker port plex-mqtt-bridge
} catch {
    Write-Host "❌ No port mappings found" -ForegroundColor Red
}

# Check if port 5000 is in use on host
Write-Host
Write-Host "🚪 Host Port 5000 Status:" -ForegroundColor Yellow
try {
    $port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($port5000) {
        Write-Host "Port 5000 is in use:" -ForegroundColor Green
        $port5000 | Format-Table LocalAddress, LocalPort, State, OwningProcess
    } else {
        Write-Host "Port 5000 is not in use on host" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Cannot check port status" -ForegroundColor Red
}

# Test connectivity from host
Write-Host
Write-Host "🌐 Testing Connectivity:" -ForegroundColor Yellow
Write-Host "Testing localhost:5000..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/status" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ HTTP Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to localhost:5000" -ForegroundColor Red
}

Write-Host "Testing 127.0.0.1:5000..."
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/status" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ HTTP Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to 127.0.0.1:5000" -ForegroundColor Red
}

# Test from inside container if it's running
Write-Host
Write-Host "🐳 Testing from inside container:" -ForegroundColor Yellow
try {
    $containerTest = docker exec plex-mqtt-bridge curl -s -o /dev/null -w "Internal HTTP Status: %{http_code}" http://localhost:5000/api/status 2>$null
    Write-Host "Internal test result: $containerTest" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot test from inside container" -ForegroundColor Red
}

# Check Docker network
Write-Host
Write-Host "🌐 Docker Network Info:" -ForegroundColor Yellow
try {
    docker network ls | Select-String "plex-mqtt"
    docker inspect plex-mqtt-network | ConvertFrom-Json | ForEach-Object { $_.Containers }
} catch {
    Write-Host "❌ Cannot inspect network" -ForegroundColor Red
}

Write-Host
Write-Host "=== Troubleshooting Complete ===" -ForegroundColor Cyan
Write-Host
Write-Host "💡 Common Solutions:" -ForegroundColor Green
Write-Host "1. Make sure container is running: docker-compose up -d"
Write-Host "2. Check Windows Firewall settings"
Write-Host "3. Try different port mapping: '8080:5000' in docker-compose.yml"
Write-Host "4. Check if another service is using port 5000"
Write-Host "5. Restart Docker Desktop"
Write-Host "6. Rebuild container: docker-compose build --no-cache"
Write-Host "7. Try binding to specific interface: host: '127.0.0.1' in config.json"
