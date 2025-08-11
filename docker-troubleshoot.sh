#!/bin/bash

# docker-troubleshoot.sh - Docker networking troubleshooting script

echo "=== Docker Container Troubleshooting ==="
echo

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

echo "✅ Docker is available"

# Check container status
echo
echo "📋 Container Status:"
docker ps -a --filter "name=plex-mqtt-bridge"

# Check container logs
echo
echo "📝 Recent Container Logs:"
docker logs --tail 20 plex-mqtt-bridge 2>/dev/null || echo "❌ Container not found or not running"

# Check port mapping
echo
echo "🔌 Port Mapping:"
docker port plex-mqtt-bridge 2>/dev/null || echo "❌ No port mappings found"

# Check if port 5000 is in use on host
echo
echo "🚪 Host Port 5000 Status:"
if command -v netstat &> /dev/null; then
    netstat -tlnp | grep :5000 || echo "Port 5000 is not in use on host"
elif command -v ss &> /dev/null; then
    ss -tlnp | grep :5000 || echo "Port 5000 is not in use on host"
else
    echo "Cannot check port status (netstat/ss not available)"
fi

# Test connectivity from host
echo
echo "🌐 Testing Connectivity:"
echo "Testing localhost:5000..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:5000/api/status 2>/dev/null || echo "❌ Cannot connect to localhost:5000"

echo "Testing 127.0.0.1:5000..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:5000/api/status 2>/dev/null || echo "❌ Cannot connect to 127.0.0.1:5000"

# Test from inside container if it's running
echo
echo "🐳 Testing from inside container:"
docker exec plex-mqtt-bridge curl -s -o /dev/null -w "Internal HTTP Status: %{http_code}\n" http://localhost:5000/api/status 2>/dev/null || echo "❌ Cannot test from inside container"

# Check Docker network
echo
echo "🌐 Docker Network Info:"
docker network ls | grep plex-mqtt
docker inspect plex-mqtt-network 2>/dev/null | grep -A 10 -B 5 "plex-mqtt-bridge" || echo "❌ Cannot inspect network"

echo
echo "=== Troubleshooting Complete ==="
echo
echo "💡 Common Solutions:"
echo "1. Make sure container is running: docker-compose up -d"
echo "2. Check firewall settings on host"
echo "3. Try different port mapping: '8080:5000' in docker-compose.yml"
echo "4. Check if another service is using port 5000"
echo "5. Restart Docker service: sudo systemctl restart docker"
echo "6. Rebuild container: docker-compose build --no-cache"
