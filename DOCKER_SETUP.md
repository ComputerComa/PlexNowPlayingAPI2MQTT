# Docker Installation and Setup Guide

## Prerequisites

### 1. Install Docker Desktop

Download and install Docker Desktop for Windows:
- Visit: https://docs.docker.com/desktop/install/windows-install/
- Download Docker Desktop for Windows
- Run the installer and follow the setup wizard
- Restart your computer when prompted

### 2. Verify Docker Installation

After installation, open PowerShell or Command Prompt and verify:

```bash
docker --version
docker-compose --version
```

You should see version information for both commands.

## Quick Start

### Method 1: Using Docker Compose with Config File

1. **Prepare your configuration:**
   ```bash
   # Copy the example configuration
   cp config.example.json config.json
   
   # Edit config.json with your settings
   # - Add your Plex token (use get_plex_token.py to get it)
   # - Configure your MQTT broker details
   ```

2. **Build and run:**
   ```bash
   docker-compose up -d
   ```

3. **Access the web interface:**
   Open http://localhost:5000 in your browser

### Method 2: Using Environment Variables

1. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration values
   ```

2. **Run with environment configuration:**
   ```bash
   docker-compose -f docker-compose.env.yml up -d
   ```

## Manual Docker Commands

### Build the image:
```bash
docker build -t plex-mqtt-bridge .
```

### Run with mounted config:
```bash
docker run -d \
  --name plex-mqtt-bridge \
  -p 5000:5000 \
  -v ${PWD}/config.json:/app/config.json:ro \
  --restart unless-stopped \
  plex-mqtt-bridge
```

### Run with environment variables:
```bash
docker run -d \
  --name plex-mqtt-bridge \
  -p 5000:5000 \
  -e PLEX_TOKEN="your_plex_token_here" \
  -e MQTT_BROKER="your.mqtt.broker.com" \
  -e MQTT_PORT="1883" \
  -e MQTT_USERNAME="your_username" \
  -e MQTT_PASSWORD="your_password" \
  --restart unless-stopped \
  plex-mqtt-bridge
```

## Container Management

### View logs:
```bash
docker-compose logs -f plex-mqtt-bridge
```

### Check status:
```bash
docker-compose ps
```

### Stop the container:
```bash
docker-compose down
```

### Restart the container:
```bash
docker-compose restart plex-mqtt-bridge
```

### Update the application:
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### 1. Container won't start
Check the logs:
```bash
docker-compose logs plex-mqtt-bridge
```

Common issues:
- Missing or invalid config.json
- Invalid Plex token
- MQTT broker connection issues
- Port 5000 already in use

### 2. Can't access web interface
- Verify the container is running: `docker-compose ps`
- Check if port 5000 is accessible: `netstat -an | findstr :5000`
- Try accessing via container IP: `docker inspect plex-mqtt-bridge`

### 3. Plex connection issues
- Verify your Plex token is correct
- Check Plex server accessibility from Docker container
- Ensure Plex server allows connections from the container network

### 4. MQTT connection issues
- Verify MQTT broker settings
- Check firewall settings
- Test MQTT connection manually

## Windows-Specific Notes

### PowerShell Commands
When running on Windows PowerShell, use these volume mount formats:

```bash
# Using current directory
docker run -v ${PWD}/config.json:/app/config.json:ro plex-mqtt-bridge

# Using absolute path
docker run -v C:/PlexNowPlayingAPI2MQTT/config.json:/app/config.json:ro plex-mqtt-bridge
```

### File Permissions
Windows Docker Desktop handles file permissions automatically, so no special setup is needed.

### Networking
Docker Desktop on Windows uses Hyper-V networking. The containers can access:
- Internet (for Plex API and external MQTT brokers)
- Local network services (for local MQTT brokers)
- Host services via `host.docker.internal`

## Advanced Configuration

### Custom Network
To create a custom Docker network:

```bash
docker network create plex-mqtt-network
docker-compose up -d
```

### Resource Limits
Add resource limits to docker-compose.yml:

```yaml
services:
  plex-mqtt-bridge:
    # ... other settings
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.5'
```

### Persistent Logs
Mount a log directory:

```yaml
services:
  plex-mqtt-bridge:
    # ... other settings
    volumes:
      - ./config.json:/app/config.json:ro
      - ./logs:/app/logs
```
