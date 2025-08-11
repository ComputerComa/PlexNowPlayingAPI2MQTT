#!/bin/bash

# entrypoint.sh - Docker entrypoint script for Plex MQTT Bridge

set -e

# Function to create config.json from environment variables if it doesn't exist
create_config_from_env() {
    if [ ! -f "/app/config.json" ] && [ -n "$PLEX_TOKEN" ] && [ -n "$MQTT_BROKER" ]; then
        echo "Creating config.json from environment variables..."
        cat > /app/config.json << EOF
{
    "plex": {
        "token": "${PLEX_TOKEN}",
        "server_name": "${PLEX_SERVER_NAME:-}"
    },
    "mqtt": {
        "broker": "${MQTT_BROKER}",
        "port": ${MQTT_PORT:-1883},
        "username": "${MQTT_USERNAME:-}",
        "password": "${MQTT_PASSWORD:-}",
        "protocol": "${MQTT_PROTOCOL:-v5}",
        "websockets": ${MQTT_WEBSOCKETS:-false},
        "ssl": ${MQTT_SSL:-false},
        "topic_strategy": "${MQTT_TOPIC_STRATEGY:-user_device_track}"
    },
    "general": {
        "polling_interval": ${POLLING_INTERVAL:-5}
    },
    "web_interface": {
        "enabled": ${WEB_INTERFACE_ENABLED:-true},
        "host": "${WEB_INTERFACE_HOST:-0.0.0.0}",
        "port": ${WEB_INTERFACE_PORT:-5000}
    }
}
EOF
        echo "Config created from environment variables."
    elif [ ! -f "/app/config.json" ]; then
        echo "ERROR: No config.json found and required environment variables not set."
        echo "Either mount a config.json file or set the following environment variables:"
        echo "  PLEX_TOKEN, MQTT_BROKER"
        echo "Optional variables: PLEX_SERVER_NAME, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD,"
        echo "  MQTT_PROTOCOL, MQTT_WEBSOCKETS, MQTT_SSL, MQTT_TOPIC_STRATEGY,"
        echo "  POLLING_INTERVAL, WEB_INTERFACE_ENABLED, WEB_INTERFACE_HOST, WEB_INTERFACE_PORT"
        exit 1
    fi
}

# Create config if needed
create_config_from_env

# Execute the main command
exec "$@"
