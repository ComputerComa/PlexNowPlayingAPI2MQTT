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
- 🌐 **Web Interface** - Real-time dashboard for monitoring active sessions
- 🐳 **Docker Ready** - Easy deployment with Docker and Docker Compose
- 🔧 **Flexible Configuration** - Support for config files and environment variables
- 🎤 **Last.fm Scrobbling** - Optional scrobbling to Last.fm with configurable thresholds
- 📊 **User/Device Tracking** - Track and persist users and devices across sessions

## Requirements

- Python 3.8+
- Plex Media Server with API access
- MQTT broker (local or remote)

## Installation

### Option 1: Docker (Recommended)

The easiest way to run the application is using Docker:

```bash
# Clone the repository
git clone https://github.com/ComputerComa/PlexNowPlayingAPI2MQTT.git
cd PlexNowPlayingAPI2MQTT

# Copy and edit configuration
cp config.example.json config.json
# Edit config.json with your Plex token and MQTT settings

# Run with Docker Compose
docker-compose up -d

# Access the web interface
# Open http://localhost:5000 in your browser
```

**Windows Users**: Use the included `start_docker.bat` script for guided setup!

See [DOCKER.md](DOCKER.md) for detailed Docker deployment instructions.

**Validation**: Run `python validate_docker.py` to check your Docker setup before deployment.

### Option 2: Local Python Installation

1. Clone the repository:
```bash
git clone https://github.com/ComputerComa/PlexNowPlayingAPI2MQTT.git
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

**Standard TCP Connection (MQTT v3.1.1):**
```json
"mqtt": {
    "broker": "localhost",
    "port": 1883,
    "use_websockets": false,
    "protocol_version": 3.1,
    "use_ssl": false
}
```

**WebSocket Connection (MQTT v3.1.1):**
```json
"mqtt": {
    "broker": "localhost", 
    "port": 9001,
    "use_websockets": true,
    "websocket_path": "/mqtt",
    "protocol_version": 3.1,
    "use_ssl": false
}
```

**WebSocket with SSL/TLS (MQTT v5):**
```json
"mqtt": {
    "broker": "mqtt.example.com",
    "port": 443,
    "use_websockets": true,
    "websocket_path": "/",
    "protocol_version": 5,
    "use_ssl": true
}
```

**MQTT v5 Enhanced Features:**
- Message expiry (30 second TTL)
- Content type specification (`application/json`)
- User properties for better message tracking
- Enhanced error reporting and connection callbacks
- QoS 1 for reliable delivery

**Common Ports:**
- **1883**: Standard MQTT TCP (unencrypted)
- **8883**: Standard MQTT TCP with SSL/TLS
- **9001**: MQTT over WebSockets (unencrypted)
- **443**: MQTT over WebSockets with SSL/TLS

### Last.fm Scrobbling (Optional)

Enable automatic scrobbling to Last.fm by adding this configuration:

```json
"lastfm": {
    "enabled": true,
    "api_key": "YOUR_LASTFM_API_KEY",
    "api_secret": "YOUR_LASTFM_API_SECRET",
    "username": "YOUR_LASTFM_USERNAME", 
    "password": "YOUR_LASTFM_PASSWORD",
    "scrobble_threshold": 0.5,
    "min_duration": 30
}
```

**Configuration Options:**
- **`enabled`** - Enable/disable Last.fm scrobbling
- **`api_key`** - Your Last.fm API key (get from https://www.last.fm/api/account/create)
- **`api_secret`** - Your Last.fm API secret
- **`username`** - Your Last.fm username
- **`password`** - Your Last.fm password (hashed before transmission)
- **`scrobble_threshold`** - Percentage of track that must be played to scrobble (0.5 = 50%)
- **`min_duration`** - Minimum track duration in seconds to be eligible for scrobbling

**Getting Last.fm API Credentials:**
Run the helper script for detailed instructions:
```bash
python get_lastfm_credentials.py
```

## MQTT Message Format

The application publishes enhanced JSON messages with progress tracking:

```json
{
    "status": "playing|paused|stopped",
    "title": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name", 
    "thumb": "thumbnail_url",
    "duration": 240000,
    "viewOffset": 30000,
    "progress_percent": 12.5,
    "duration_formatted": "4:00",
    "position_formatted": "0:30",
    "remaining_formatted": "3:30",
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

### **Progress Tracking Fields:**
- **`progress_percent`** - Percentage through the track (0.0-100.0)
- **`duration_formatted`** - Total track length in MM:SS or HH:MM:SS format
- **`position_formatted`** - Current position in MM:SS or HH:MM:SS format  
- **`remaining_formatted`** - Time remaining in MM:SS or HH:MM:SS format
- **`duration`** - Total duration in milliseconds (original)
- **`viewOffset`** - Current position in milliseconds (original)
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

## Multi-Session Handling

When you're listening to music in multiple places simultaneously, the application offers several strategies:

### **Session Strategies:**

```json
"multi_session_handling": {
    "strategy": "all",           // "all", "priority_user", "first_only", "user_filter", "most_recent"
    "user_filter": ["Alice"],    // Only publish sessions from these users
    "priority_user": "Alice"     // Prefer this user's sessions
}
```

**Strategy Options:**
- **`"all"`** - Publish all active sessions (default)
- **`"priority_user"`** - Only publish from priority user, fallback to first session
- **`"first_only"`** - Only publish the first detected session
- **`"user_filter"`** - Only publish sessions from specific users
- **`"most_recent"`** - Only publish the session with most recent activity

### **Topic Strategies:**

```json
"mqtt": {
    "topic": "plex/playing_status", 
    "topic_strategy": "user_device_track"   // "single", "per_user", "per_device", "hierarchical", "user_device_track"
}
```

**Topic Strategy Options:**
- **`"single"`** - All sessions → `plex/playing_status`
- **`"per_user"`** - Per user → `plex/playing_status/Alice`, `plex/playing_status/Bob`
- **`"per_device"`** - Per session → `plex/playing_status/session_123`
- **`"hierarchical"`** - Combined → `plex/playing_status/Alice/session_123`
- **`"user_device_track"`** - Full hierarchy → `plex/playing_status/ComputerComa/iPhone/DATA`

### **USER/DEVICE/DATA Format Example:**

With `"topic_strategy": "user_device_track"`, messages are published to:
```
plex/playing_status/ComputerComa/iPhone/DATA
plex/playing_status/Alice/ChromeCast/DATA
plex/playing_status/Bob/PlexAmp/DATA
```

**Topic Structure:**
- **Base Topic**: `plex/playing_status`
- **User**: Plex username (spaces replaced with underscores)
- **Device**: Player device name (iPhone, ChromeCast, PlexAmp, etc.)
- **DATA**: Literal word "DATA" (contains the JSON payload)

**Special Topics:**
- **Stopped Status**: `plex/playing_status/system/stopped/DATA` (when no music playing)
- **Session Summary**: `plex/playing_status/summary` (overview of all sessions)

### **Session Summary:**

Enable `"publish_summary": true` to get an overview of all active sessions:

```json
// Published to: nowplaying/summary
{
    "active_sessions": 3,
    "users": ["Alice", "Bob", "ComputerComa"],
    "sessions": [
        {"user": "Alice", "title": "Song A", "status": "playing"},
        {"user": "Bob", "title": "Song B", "status": "paused"},
        {"user": "ComputerComa", "title": "Song C", "status": "playing"}
    ]
}
```

## License

MIT License
