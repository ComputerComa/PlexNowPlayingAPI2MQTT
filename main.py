#!/usr/bin/env python3
"""
Plex Now Playing API to MQTT Bridge
Monitors Plex Media Server for currently playing music and publishes to MQTT
Uses the official PlexAPI library for better integration
"""

import json
import time
import logging
import sys
from datetime import datetime
from typing import Dict, Optional, Any, List

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from plexapi.server import PlexServer
from plexapi.exceptions import PlexApiException, Unauthorized


class PlexMQTTBridge:
    """Main class for bridging Plex API to MQTT"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the bridge with configuration"""
        self.config = self._load_config(config_file)
        self.mqtt_client = None
        self.plex = None
        self.last_status = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if self.config.get('debug', False) else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_file} not found. Please copy config.example.json to config.json")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in config file: {e}")
            sys.exit(1)
    
    def _setup_plex(self) -> bool:
        """Setup Plex server connection"""
        try:
            plex_config = self.config['plex']
            
            # Connect to Plex server
            self.plex = PlexServer(
                plex_config['url'], 
                plex_config['token']
            )
            
            # Test connection
            server_info = self.plex.account()
            self.logger.info(f"Connected to Plex server: {self.plex.friendlyName}")
            self.logger.info(f"Server version: {self.plex.version}")
            self.logger.info(f"Account: {server_info.username if server_info else 'Unknown'}")
            
            return True
            
        except Unauthorized:
            self.logger.error("Plex authentication failed. Please check your token.")
            return False
        except PlexApiException as e:
            self.logger.error(f"Plex API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to Plex server: {e}")
            return False
    
    def _setup_mqtt(self) -> bool:
        """Setup MQTT client connection"""
        try:
            mqtt_config = self.config['mqtt']
            
            # Check if WebSockets should be used
            if mqtt_config.get('use_websockets', False):
                self.mqtt_client = mqtt.Client(transport="websockets")
                self.logger.info("Using MQTT over WebSockets")
            else:
                self.mqtt_client = mqtt.Client()
                self.logger.info("Using standard MQTT TCP connection")
            
            # Set credentials if provided
            if mqtt_config.get('username') and mqtt_config.get('password'):
                self.mqtt_client.username_pw_set(
                    mqtt_config['username'], 
                    mqtt_config['password']
                )
            
            # For WebSockets, we may need to set the path
            if mqtt_config.get('use_websockets', False) and mqtt_config.get('websocket_path'):
                # Set WebSocket path if specified
                self.mqtt_client.ws_set_options(path=mqtt_config['websocket_path'])
            
            # Connect to broker
            self.mqtt_client.connect(
                mqtt_config['broker'], 
                mqtt_config['port'], 
                60
            )
            self.mqtt_client.loop_start()
            
            connection_type = "WebSocket" if mqtt_config.get('use_websockets', False) else "TCP"
            self.logger.info(f"Connected to MQTT broker at {mqtt_config['broker']}:{mqtt_config['port']} via {connection_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _get_music_sessions(self) -> List[Dict]:
        """Get current music sessions from Plex"""
        try:
            sessions = self.plex.sessions()
            music_sessions = []
            
            for session in sessions:
                # Only process music/track sessions
                if session.type == 'track':
                    music_info = self._extract_music_info_from_session(session)
                    if music_info:
                        music_sessions.append(music_info)
            
            return music_sessions
            
        except PlexApiException as e:
            self.logger.error(f"Error fetching Plex sessions: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching sessions: {e}")
            return []
    
    def _extract_music_info_from_session(self, session) -> Optional[Dict]:
        """Extract music information from a Plex session object"""
        try:
            # Get player state
            player_state = 'unknown'
            if hasattr(session, 'players') and session.players:
                player = session.players[0]
                player_state = player.state if hasattr(player, 'state') else 'unknown'
            
            # Extract track information
            info = {
                'status': player_state,
                'title': getattr(session, 'title', 'Unknown'),
                'artist': getattr(session, 'grandparentTitle', 'Unknown Artist'),
                'album': getattr(session, 'parentTitle', 'Unknown Album'),
                'duration': getattr(session, 'duration', 0),
                'viewOffset': getattr(session, 'viewOffset', 0),
                'user': session.usernames[0] if session.usernames else 'Unknown',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Get thumbnail URL
            thumb_url = ''
            if hasattr(session, 'thumb') and session.thumb:
                # PlexAPI automatically handles the full URL construction
                thumb_url = session.thumbUrl
            elif hasattr(session, 'art') and session.art:
                thumb_url = session.artUrl
            
            info['thumb'] = thumb_url
            
            # Add additional metadata if available
            if hasattr(session, 'year') and session.year:
                info['year'] = session.year
            
            if hasattr(session, 'parentIndex') and session.parentIndex:
                info['track_number'] = session.parentIndex
            
            if hasattr(session, 'index') and session.index:
                info['disc_number'] = session.index
            
            # Add bitrate and format info if available
            if hasattr(session, 'media') and session.media:
                media = session.media[0] if session.media else None
                if media:
                    if hasattr(media, 'bitrate') and media.bitrate:
                        info['bitrate'] = media.bitrate
                    if hasattr(media, 'audioCodec') and media.audioCodec:
                        info['codec'] = media.audioCodec
            
            # Add session key for tracking
            if hasattr(session, 'sessionKey'):
                info['session_key'] = session.sessionKey
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error extracting music info from session: {e}")
            return None
    
    def _publish_to_mqtt(self, data: Dict) -> bool:
        """Publish data to MQTT broker"""
        try:
            if not self.mqtt_client:
                return False
            
            topic = self.config['mqtt']['topic']
            payload = json.dumps(data, indent=2 if self.config.get('debug', False) else None)
            
            result = self.mqtt_client.publish(topic, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                self.logger.error(f"Failed to publish to MQTT: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing to MQTT: {e}")
            return False
    
    def _publish_stopped_status(self):
        """Publish stopped status when no music is playing"""
        stopped_data = {
            'status': 'stopped',
            'title': '',
            'artist': '',
            'album': '',
            'thumb': '',
            'duration': 0,
            'viewOffset': 0,
            'user': '',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        self._publish_to_mqtt(stopped_data)
    
    def _should_publish_update(self, music_info: Dict) -> bool:
        """Determine if we should publish an update based on changes"""
        session_key = f"{music_info['user']}_{music_info.get('session_key', music_info['title'])}"
        
        # Always publish if this is a new session
        if session_key not in self.last_status:
            return True
        
        last_info = self.last_status[session_key]
        
        # Publish if status changed
        if last_info.get('status') != music_info['status']:
            return True
        
        # Publish if track changed
        if (last_info.get('title') != music_info['title'] or 
            last_info.get('artist') != music_info['artist']):
            return True
        
        # Publish if viewOffset changed significantly (more than 5 seconds)
        offset_diff = abs(music_info['viewOffset'] - last_info.get('viewOffset', 0))
        if offset_diff > 5000:  # 5 seconds in milliseconds
            return True
        
        return False
    
    def run(self):
        """Main execution loop"""
        self.logger.info("Starting Plex to MQTT bridge...")
        
        # Setup Plex connection
        if not self._setup_plex():
            sys.exit(1)
        
        # Setup MQTT connection
        if not self._setup_mqtt():
            sys.exit(1)
        
        polling_interval = self.config.get('polling_interval', 5)
        self.logger.info(f"Polling Plex every {polling_interval} seconds")
        
        try:
            while True:
                # Get current music sessions
                music_sessions = self._get_music_sessions()
                
                # Track which sessions are still active
                current_session_keys = set()
                
                if music_sessions:
                    for music_info in music_sessions:
                        session_key = f"{music_info['user']}_{music_info.get('session_key', music_info['title'])}"
                        current_session_keys.add(session_key)
                        
                        # Only publish if there are significant changes
                        if self._should_publish_update(music_info):
                            self._publish_to_mqtt(music_info)
                            self.logger.info(f"Published update for {music_info['user']}: {music_info['artist']} - {music_info['title']} ({music_info['status']})")
                        
                        # Update last status
                        self.last_status[session_key] = music_info
                else:
                    # No music playing, publish stopped status if not already done
                    if not self.last_status.get('_stopped', False):
                        self._publish_stopped_status()
                        self.logger.info("No music sessions found - published stopped status")
                        # Clear previous sessions and mark as stopped
                        self.last_status = {'_stopped': True}
                
                # Clean up old sessions that are no longer active
                if current_session_keys:
                    # Remove the stopped flag if we have active sessions
                    self.last_status.pop('_stopped', None)
                    
                    # Remove sessions that are no longer active
                    old_keys = set(self.last_status.keys()) - current_session_keys
                    for old_key in old_keys:
                        if not old_key.startswith('_'):  # Don't remove internal flags
                            self.last_status.pop(old_key, None)
                
                time.sleep(polling_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()


def main():
    """Entry point"""
    bridge = PlexMQTTBridge()
    bridge.run()


if __name__ == "__main__":
    main()
