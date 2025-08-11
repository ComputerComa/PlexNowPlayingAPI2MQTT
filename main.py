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
from threading import Thread

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from plexapi.server import PlexServer
from plexapi.exceptions import PlexApiException, Unauthorized
from web_interface import WebInterface


class PlexMQTTBridge:
    """Main class for bridging Plex API to MQTT"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the bridge with configuration"""
        self.config = self._load_config(config_file)
        self.mqtt_client = None
        self.plex = None
        self.last_status = {}
        self.start_time = datetime.now()
        self.web_interface = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if self.config.get('debug', False) else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup web interface if enabled
        if self.config.get('web_interface', {}).get('enabled', True):
            self.web_interface = WebInterface(self)
            self._start_web_server()
        
    def _start_web_server(self):
        """Start the web server in a separate thread"""
        try:
            web_config = self.config.get('web_interface', {})
            host = web_config.get('host', '0.0.0.0')
            port = web_config.get('port', 5000)
            
            def run_server():
                self.web_interface.run(host=host, port=port, debug=False)
            
            web_thread = Thread(target=run_server, daemon=True)
            web_thread.start()
            
            self.logger.info(f"Web interface started at http://{host}:{port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start web interface: {e}")
        
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
        """Setup MQTT client connection with v5 support"""
        try:
            mqtt_config = self.config['mqtt']
            
            # Determine MQTT protocol version
            protocol_version = mqtt_config.get('protocol_version', 3.1)
            if protocol_version == 5:
                mqtt_protocol = mqtt.MQTTv5
                callback_api_version = CallbackAPIVersion.VERSION2
                self.logger.info("Using MQTT v5 protocol")
            else:
                mqtt_protocol = mqtt.MQTTv311
                callback_api_version = CallbackAPIVersion.VERSION1
                self.logger.info("Using MQTT v3.1.1 protocol")
            
            # Check if WebSockets should be used
            if mqtt_config.get('use_websockets', False):
                self.mqtt_client = mqtt.Client(
                    callback_api_version=callback_api_version,
                    protocol=mqtt_protocol,
                    transport="websockets"
                )
                self.logger.info("Using MQTT over WebSockets")
            else:
                self.mqtt_client = mqtt.Client(
                    callback_api_version=callback_api_version,
                    protocol=mqtt_protocol
                )
                self.logger.info("Using standard MQTT TCP connection")
            
            # Set credentials if provided
            if mqtt_config.get('username') and mqtt_config.get('password'):
                self.mqtt_client.username_pw_set(
                    mqtt_config['username'], 
                    mqtt_config['password']
                )
            
            # Configure SSL/TLS if enabled
            if mqtt_config.get('use_ssl', False):
                self.mqtt_client.tls_set()
                self.logger.info("SSL/TLS enabled for MQTT connection")
            
            # For WebSockets, set the path and headers
            if mqtt_config.get('use_websockets', False):
                websocket_path = mqtt_config.get('websocket_path', '/mqtt')
                
                # Set WebSocket options
                if protocol_version == 5:
                    # MQTT v5 WebSocket setup
                    self.mqtt_client.ws_set_options(
                        path=websocket_path,
                        headers={"Sec-WebSocket-Protocol": "mqtt"}
                    )
                else:
                    # MQTT v3.1.1 WebSocket setup
                    self.mqtt_client.ws_set_options(path=websocket_path)
            
            # Set up callbacks for better debugging
            def on_connect(client, userdata, flags, rc, properties=None):
                if protocol_version == 5:
                    if rc == 0:
                        self.logger.info("MQTT v5 connection successful")
                    else:
                        self.logger.error(f"MQTT v5 connection failed with code {rc}")
                else:
                    if rc == 0:
                        self.logger.info("MQTT v3.1.1 connection successful")
                    else:
                        self.logger.error(f"MQTT v3.1.1 connection failed with code {rc}")
            
            def on_disconnect(client, userdata, flags=None, rc=None, properties=None):
                self.logger.warning(f"MQTT disconnected with code {rc}")
            
            def on_publish(client, userdata, mid, rc=None, properties=None):
                self.logger.debug(f"Message {mid} published successfully")
            
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_disconnect = on_disconnect
            self.mqtt_client.on_publish = on_publish
            
            # Connect to broker
            self.mqtt_client.connect(
                mqtt_config['broker'], 
                mqtt_config['port'], 
                60
            )
            self.mqtt_client.loop_start()
            
            connection_type = "WebSocket" if mqtt_config.get('use_websockets', False) else "TCP"
            ssl_status = " with SSL/TLS" if mqtt_config.get('use_ssl', False) else ""
            self.logger.info(f"Connecting to MQTT broker at {mqtt_config['broker']}:{mqtt_config['port']} via {connection_type}{ssl_status}")
            
            # Wait a moment for connection to establish
            import time
            time.sleep(2)
            
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
            device_name = 'unknown'
            
            if hasattr(session, 'players') and session.players:
                player = session.players[0]
                player_state = player.state if hasattr(player, 'state') else 'unknown'
                
                # Extract device information
                if hasattr(player, 'title'):
                    device_name = player.title
                elif hasattr(player, 'device'):
                    device_name = player.device
                elif hasattr(player, 'product'):
                    device_name = player.product
                elif hasattr(player, 'platform'):
                    device_name = player.platform
            
            # Also try to get device info directly from session
            if device_name == 'unknown':
                if hasattr(session, 'player') and hasattr(session.player, 'title'):
                    device_name = session.player.title
                elif hasattr(session, 'device'):
                    device_name = session.device
            
            # Clean up device name for MQTT topic compatibility
            device_clean = device_name.replace(' ', '_').replace('/', '_').replace('#', '').replace('+', '').replace('$', '')
            
            # Extract basic track information
            duration = getattr(session, 'duration', 0)
            view_offset = getattr(session, 'viewOffset', 0)
            
            # Calculate progress percentage
            progress_percent = 0.0
            if duration > 0:
                progress_percent = (view_offset / duration) * 100
                # Round to 2 decimal places
                progress_percent = round(progress_percent, 2)
            
            # Extract track information
            info = {
                'status': player_state,
                'title': getattr(session, 'title', 'Unknown'),
                'artist': getattr(session, 'grandparentTitle', 'Unknown Artist'),
                'album': getattr(session, 'parentTitle', 'Unknown Album'),
                'duration': duration,
                'viewOffset': view_offset,
                'progress_percent': progress_percent,
                'device': device_clean,
                'device_original': device_name,
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
            
            # Add human-readable time formats
            info['duration_formatted'] = self._format_duration(duration)
            info['position_formatted'] = self._format_duration(view_offset)
            info['remaining_formatted'] = self._format_duration(duration - view_offset)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error extracting music info from session: {e}")
            return None
    
    def _format_duration(self, milliseconds: int) -> str:
        """Convert milliseconds to human-readable format (MM:SS or HH:MM:SS)"""
        if milliseconds <= 0:
            return "0:00"
        
        total_seconds = milliseconds // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def _get_topic_for_session(self, music_info: Dict) -> str:
        """Get the appropriate MQTT topic for a session based on strategy"""
        base_topic = self.config['mqtt']['topic']
        topic_strategy = self.config['mqtt'].get('topic_strategy', 'single')
        
        if topic_strategy == 'user_device_track':
            # Format: USER/DEVICE/DATA (where DATA is literal)
            user = music_info['user'].replace(' ', '_').replace('/', '_')
            device = music_info.get('device', music_info.get('session_key', 'unknown')).replace(' ', '_').replace('/', '_')
            return f"{base_topic}/{user}/{device}/DATA"
        elif topic_strategy == 'per_user':
            # Topic per user: nowplaying/ComputerComa
            return f"{base_topic}/{music_info['user']}"
        elif topic_strategy == 'per_device':
            # Topic per device/session: nowplaying/device_123
            session_key = music_info.get('session_key', 'unknown')
            return f"{base_topic}/session_{session_key}"
        elif topic_strategy == 'hierarchical':
            # Hierarchical: nowplaying/ComputerComa/session_123
            session_key = music_info.get('session_key', 'unknown')
            return f"{base_topic}/{music_info['user']}/session_{session_key}"
        else:
            # Default single topic
            return base_topic
    
    def _filter_sessions(self, music_sessions: List[Dict]) -> List[Dict]:
        """Filter sessions based on configuration"""
        if not music_sessions:
            return music_sessions
        
        multi_config = self.config.get('multi_session_handling', {})
        strategy = multi_config.get('strategy', 'all')
        
        if strategy == 'all':
            # Return all sessions
            return music_sessions
        
        elif strategy == 'priority_user':
            # Only return sessions from priority user, fallback to first if not found
            priority_user = multi_config.get('priority_user', '')
            if priority_user:
                priority_sessions = [s for s in music_sessions if s['user'] == priority_user]
                if priority_sessions:
                    return priority_sessions
            # Fallback to first session if priority user not found
            return music_sessions[:1] if music_sessions else []
        
        elif strategy == 'first_only':
            # Only return the first session
            return music_sessions[:1] if music_sessions else []
        
        elif strategy == 'user_filter':
            # Filter by specific users
            allowed_users = multi_config.get('user_filter', [])
            if allowed_users:
                return [s for s in music_sessions if s['user'] in allowed_users]
            return music_sessions
        
        elif strategy == 'most_recent':
            # Return the session with the highest viewOffset (most recent activity)
            if len(music_sessions) > 1:
                most_recent = max(music_sessions, key=lambda s: s.get('viewOffset', 0))
                return [most_recent]
            return music_sessions
        
        else:
            return music_sessions
    
    def _publish_session_summary(self, music_sessions: List[Dict]):
        """Publish a summary of all active sessions"""
        summary_topic = f"{self.config['mqtt']['topic']}/summary"
        
        summary_data = {
            'active_sessions': len(music_sessions),
            'users': list(set(s['user'] for s in music_sessions)),
            'sessions': [
                {
                    'user': s['user'],
                    'title': s['title'],
                    'artist': s['artist'],
                    'status': s['status'],
                    'session_key': s.get('session_key', 'unknown')
                } for s in music_sessions
            ],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        mqtt_config = self.config['mqtt']
        if mqtt_config.get('protocol_version') == 5:
            from paho.mqtt.properties import Properties
            from paho.mqtt.packettypes import PacketTypes
            
            properties = Properties(PacketTypes.PUBLISH)
            properties.MessageExpiryInterval = 30
            properties.ContentType = "application/json"
            properties.UserProperty = [
                ("source", "PlexNowPlayingAPI2MQTT"),
                ("message_type", "summary")
            ]
            
            result = self.mqtt_client.publish(summary_topic, json.dumps(summary_data), qos=1, properties=properties)
        else:
            result = self.mqtt_client.publish(summary_topic, json.dumps(summary_data), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.logger.debug(f"Published session summary: {len(music_sessions)} active sessions")
    
    def _publish_to_mqtt(self, data: Dict, topic: str = None) -> bool:
        """Publish data to MQTT broker with v5 support"""
        try:
            if not self.mqtt_client:
                return False
            
            if topic is None:
                topic = self._get_topic_for_session(data)
            
            payload = json.dumps(data, indent=2 if self.config.get('debug', False) else None)
            
            # Check if we're using MQTT v5 for enhanced features
            mqtt_config = self.config['mqtt']
            if mqtt_config.get('protocol_version') == 5:
                # MQTT v5 allows for message properties
                from paho.mqtt.properties import Properties
                from paho.mqtt.packettypes import PacketTypes
                
                properties = Properties(PacketTypes.PUBLISH)
                properties.MessageExpiryInterval = 30  # Message expires in 30 seconds
                properties.ContentType = "application/json"
                
                # Add user properties for better tracking
                properties.UserProperty = [
                    ("source", "PlexNowPlayingAPI2MQTT"),
                    ("version", "1.0"),
                    ("status", data.get('status', 'unknown')),
                    ("user", data.get('user', 'unknown'))
                ]
                
                result = self.mqtt_client.publish(topic, payload, qos=1, properties=properties)
            else:
                # Standard MQTT v3.1.1 publish
                result = self.mqtt_client.publish(topic, payload, qos=1)
            
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
            'progress_percent': 0.0,
            'duration_formatted': '0:00',
            'position_formatted': '0:00',
            'remaining_formatted': '0:00',
            'device': 'system',
            'device_original': 'System',
            'user': 'system',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # For stopped status, publish to base topic since we don't have specific user/device/track
        base_topic = self.config['mqtt']['topic']
        stopped_topic = f"{base_topic}/system/stopped/DATA"
        
        self._publish_to_mqtt(stopped_data, stopped_topic)
    
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
                all_music_sessions = self._get_music_sessions()
                
                # Apply filtering based on configuration
                music_sessions = self._filter_sessions(all_music_sessions)
                
                # Track which sessions are still active
                current_session_keys = set()
                active_web_sessions = set()
                
                if music_sessions:
                    # Publish individual session updates
                    for music_info in music_sessions:
                        session_key = f"{music_info['user']}_{music_info.get('session_key', music_info['title'])}"
                        web_session_key = f"{music_info['user']}_{music_info.get('device', 'unknown')}"
                        current_session_keys.add(session_key)
                        active_web_sessions.add(web_session_key)
                        
                        # Only publish if there are significant changes
                        if self._should_publish_update(music_info):
                            topic = self._get_topic_for_session(music_info)
                            self._publish_to_mqtt(music_info, topic)
                            
                            self.logger.info(f"Published update for {music_info['user']}: {music_info['artist']} - {music_info['title']} ({music_info['status']}) to {topic}")
                        
                        # Update web interface session data
                        if self.web_interface:
                            topic = self._get_topic_for_session(music_info)
                            self.web_interface.update_session(music_info, topic)
                        
                        # Update last status
                        self.last_status[session_key] = music_info
                    
                    # Publish session summary if we have multiple sessions or summary is enabled
                    if len(all_music_sessions) > 1 or self.config.get('publish_summary', False):
                        self._publish_session_summary(all_music_sessions)
                        
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
                    
                    # Clean up inactive web sessions
                    if self.web_interface:
                        self.web_interface.clear_inactive_sessions(active_web_sessions)
                else:
                    # Clear all web sessions when no music is playing
                    if self.web_interface:
                        self.web_interface.current_sessions.clear()
                
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
