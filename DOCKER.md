# Docker Deployment Guide

This guide explains how to run the Plex MQTT Bridge using Docker.

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ComputerComa/PlexNowPlayingAPI2MQTT.git
   cd PlexNowPlayingAPI2MQTT
   ```

2. **Create your configuration:**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your Plex token and MQTT settings
   ```

3. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Access the web interface:**
   Open http://localhost:5000 in your browser

### Option 2: Using Environment Variables

1. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Run with Docker Compose using environment variables:**
   ```bash
   docker-compose -f docker-compose.env.yml up -d
   ```

### Option 3: Direct Docker Run

```bash
# Build the image
docker build -t plex-mqtt-bridge .

# Run with mounted config file
docker run -d \
  --name plex-mqtt-bridge \
  -p 5000:5000 \
  -v $(pwd)/config.json:/app/config.json:ro \
  --restart unless-stopped \
  plex-mqtt-bridge

# Or run with environment variables
docker run -d \
  --name plex-mqtt-bridge \
  -p 5000:5000 \
  -e PLEX_TOKEN="your_token_here" \
  -e MQTT_BROKER="your.broker.com" \
  -e MQTT_PORT="1883" \
  -e MQTT_USERNAME="username" \
  -e MQTT_PASSWORD="password" \
  --restart unless-stopped \
  plex-mqtt-bridge
```

## Configuration Methods

### Method 1: Config File (config.json)
Mount your `config.json` file as a read-only volume:
```yaml
volumes:
  - ./config.json:/app/config.json:ro
```

### Method 2: Environment Variables
Set the following environment variables:

#### Required:
- `PLEX_TOKEN`: Your Plex authentication token
- `MQTT_BROKER`: MQTT broker hostname/IP

#### Optional:
- `PLEX_SERVER_NAME`: Name of your Plex server
- `MQTT_PORT`: MQTT broker port (default: 1883)
- `MQTT_USERNAME`: MQTT username
- `MQTT_PASSWORD`: MQTT password
- `MQTT_PROTOCOL`: MQTT protocol version (default: v5)
- `MQTT_WEBSOCKETS`: Use WebSockets (default: false)
- `MQTT_SSL`: Use SSL/TLS (default: false)
- `MQTT_TOPIC_STRATEGY`: Topic strategy (default: user_device_track)
- `POLLING_INTERVAL`: Polling interval in seconds (default: 5)
- `WEB_INTERFACE_ENABLED`: Enable web interface (default: true)
- `WEB_INTERFACE_HOST`: Web interface host (default: 0.0.0.0)
- `WEB_INTERFACE_PORT`: Web interface port (default: 5000)

## Docker Compose Files

### Basic docker-compose.yml
Uses mounted config.json file:
```yaml
version: '3.8'
services:
  plex-mqtt-bridge:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./config.json:/app/config.json:ro
    restart: unless-stopped
```

### docker-compose.env.yml
Uses environment variables:
```yaml
version: '3.8'
services:
  plex-mqtt-bridge:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    restart: unless-stopped
```

## Container Management

### View logs:
```bash
docker-compose logs -f plex-mqtt-bridge
```

### Restart container:
```bash
docker-compose restart plex-mqtt-bridge
```

### Stop container:
```bash
docker-compose down
```

### Update container:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Health Checks

The container includes a health check that monitors the web interface:
- **Endpoint**: `http://localhost:5000/api/status`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 40 seconds

Check health status:
```bash
docker-compose ps
```

## Troubleshooting

### Check container status:
```bash
docker-compose ps
```

### View detailed logs:
```bash
docker-compose logs --tail=100 plex-mqtt-bridge
```

### Access container shell:
```bash
docker-compose exec plex-mqtt-bridge bash
```

### Test Plex token inside container:
```bash
docker-compose exec plex-mqtt-bridge python get_plex_token.py
```

### Permission issues with logs:
If you encounter permission errors when writing to logs:

**On Linux/macOS:**
```bash
# Create logs directory with proper permissions
mkdir -p logs
sudo chown -R 1000:1000 logs
```

**On Windows:**
```powershell
# Create logs directory (usually no permission issues on Windows)
New-Item -ItemType Directory -Path "logs" -Force
```

**Alternative:** Disable file logging in `config.json`:
```json
{
  "logging": {
    "file_enabled": false
  }
}
```

## Logging and Persistence

The application supports file logging with automatic rotation. Logs are persisted using Docker volumes:

### Volume Mounts
- `./logs:/app/logs` - Application logs with rotation
- `./tracking_data:/app/tracking_data` - User/device tracking persistence  
- `./config.json:/app/config.json:ro` - Configuration (read-only)

### Log Configuration
Configure logging in `config.json`:
```json
{
  "logging": {
    "file_enabled": true,
    "directory": "logs",
    "filename": "plex_mqtt_bridge.log", 
    "max_file_size_mb": 10,
    "backup_count": 5,
    "format": "%(asctime)s - %(levelname)s - %(message)s"
  }
}
```

### Log Rotation
- **Max file size**: 10MB (configurable)
- **Backup count**: 5 files (configurable)
- **Location**: `./logs/plex_mqtt_bridge.log` (host) → `/app/logs/plex_mqtt_bridge.log` (container)

### Viewing Logs
```bash
# View current log file
tail -f logs/plex_mqtt_bridge.log

# View Docker container logs
docker-compose logs -f plex-mqtt-bridge

# View logs inside container
docker-compose exec plex-mqtt-bridge tail -f /app/logs/plex_mqtt_bridge.log
```

## Security Considerations

1. **Non-root user**: Container runs as non-root user for security
2. **Read-only config**: Config file is mounted read-only
3. **Network isolation**: Uses Docker network for service isolation
4. **Environment variables**: Sensitive data via environment variables (not in image layers)

## Resource Usage

- **Image size**: ~150MB (Python 3.11 slim + dependencies)
- **Memory**: ~50-100MB runtime
- **CPU**: Minimal (polling-based)
- **Network**: Outbound only (Plex API + MQTT broker)

## Production Deployment

For production use:

1. **Use environment variables** for sensitive configuration
2. **Set up proper logging** with log rotation
3. **Use reverse proxy** (nginx/traefik) for web interface
4. **Monitor health checks** and set up alerts
5. **Regular backups** of configuration
6. **Update strategy** for security patches
