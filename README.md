# Plex Now Playing API to MQTT

A Python application that connects to the Plex API to monitor currently playing music and publishes the information to an MQTT broker for consumption by companion applications.

Built using the official [PlexAPI](https://python-plexapi.readthedocs.io/) library for robust and reliable Plex integration.

## Features

- 🎵 **Real-time Music Monitoring** - Uses PlexAPI for efficient session tracking
- 📡 **MQTT Publishing** - Supports both TCP and WebSocket connections
- 🔄 **Smart Updates** - Only publishes when significant changes occur
- 👥 **Multi-user Support** - Handles multiple concurrent Plex users
- 🎛️ **Rich Metadata** - Includes track info, artwork, bitrate, and more
- ⚙️ **Configurable** - Customizable polling intervals and connection settings

## Requirements

- Python 3.8+
- Plex Media Server with API access
- MQTT broker (local or remote)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PlexNowPlayingAPI2MQTT
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application by copying and editing the configuration file:
```bash
cp config.example.json config.json
```

4. Get your Plex token:
```bash
python get_plex_token.py
```

5. Run the application:
```bash
python main.py
```

## Configuration

Edit `config.json` with your Plex and MQTT settings:

```json
{
    "plex": {
        "url": "http://your-plex-server:32400",
        "token": "your-plex-token"
    },
    "mqtt": {
        "broker": "localhost",
        "port": 1883,
        "topic": "plex/nowplaying",
        "username": "",
        "password": "",
        "use_websockets": false,
        "websocket_path": "/mqtt"
    },
    "polling_interval": 5
}
```

### MQTT Connection Options

**Standard TCP Connection (default):**
```json
"mqtt": {
    "broker": "localhost",
    "port": 1883,
    "use_websockets": false
}
```

**WebSocket Connection:**
```json
"mqtt": {
    "broker": "localhost", 
    "port": 9001,
    "use_websockets": true,
    "websocket_path": "/mqtt"
}
```

**Common WebSocket Ports:**
- Port 9001: Standard MQTT over WebSockets
- Port 8083: Alternative WebSocket port
- Port 443: MQTT over WebSockets with SSL/TLS

## MQTT Message Format

The application publishes enhanced JSON messages to the configured MQTT topic:

```json
{
    "status": "playing|paused|stopped",
    "title": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "thumb": "thumbnail_url",
    "duration": 240000,
    "viewOffset": 30000,
    "user": "username",
    "timestamp": "2025-08-11T12:00:00Z",
    "year": 2023,
    "track_number": 5,
    "disc_number": 1,
    "bitrate": 320,
    "codec": "mp3",
    "session_key": "12345"
}
```

### Enhanced Features with PlexAPI

- **Automatic URL Construction** - Thumbnail URLs are automatically formatted
- **Rich Metadata** - Includes year, track numbers, bitrate, and codec information
- **Session Tracking** - Uses session keys for better state management
- **Error Handling** - Robust connection handling and automatic reconnection
- **Server Information** - Logs server details and account information on startup

## Token Management

### Generate New Token:
```bash
python get_plex_token.py
```

### Test Existing Token:
```bash
python get_plex_token.py test
```

The token generator will also list all available Plex servers on your account.

## License

MIT License
