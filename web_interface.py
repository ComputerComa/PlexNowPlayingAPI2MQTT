#!/usr/bin/env python3
"""
Web interface for Plex MQTT Bridge status monitoring
"""

from flask import Flask, render_template, jsonify
from datetime import datetime
from threading import Thread
import json


class WebInterface:
    """Simple web interface for monitoring the Plex MQTT Bridge"""
    
    def __init__(self, bridge_instance):
        self.bridge = bridge_instance
        self.app = Flask(__name__)
        self.current_sessions = {}
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main status page"""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for current status"""
            tracking_data = self.bridge.get_tracked_users_and_devices()
            status_data = {
                'server_connected': self.bridge.plex is not None,
                'mqtt_connected': self.bridge.mqtt_client is not None and self.bridge.mqtt_client.is_connected(),
                'server_name': getattr(self.bridge.plex, 'friendlyName', 'Unknown') if self.bridge.plex else 'Not Connected',
                'server_version': getattr(self.bridge.plex, 'version', 'Unknown') if self.bridge.plex else 'Unknown',
                'mqtt_broker': self.bridge.config['mqtt']['broker'],
                'mqtt_port': self.bridge.config['mqtt']['port'],
                'mqtt_protocol': f"MQTT v{self.bridge.config['mqtt'].get('protocol_version', '3.1')}",
                'websockets': self.bridge.config['mqtt'].get('use_websockets', False),
                'ssl': self.bridge.config['mqtt'].get('use_ssl', False),
                'topic_strategy': self.bridge.config['mqtt'].get('topic_strategy', 'single'),
                'polling_interval': self.bridge.config.get('polling_interval', 5),
                'uptime': self.get_uptime(),
                'active_sessions_count': len([s for s in self.current_sessions.values() if s.get('status') in ['playing', 'paused']]),
                'total_sessions': len(self.current_sessions),
                'tracked_users_count': tracking_data['users_count'],
                'tracked_devices_count': tracking_data['devices_count'],
                'lastfm_enabled': self.bridge.config.get('lastfm', {}).get('enabled', False),
                'lastfm_connected': self.bridge.lastfm_network is not None,
                'lastfm_username': self.bridge.config.get('lastfm', {}).get('username', '') if self.bridge.config.get('lastfm', {}).get('enabled', False) else None,
                'homeassistant_enabled': self.bridge.config.get('homeassistant', {}).get('enabled', False),
                'homeassistant_discovered_entities': len(self.bridge.ha_sensors) if hasattr(self.bridge, 'ha_sensors') else 0
            }
            return jsonify(status_data)
        
        @self.app.route('/api/sessions')
        def api_sessions():
            """API endpoint for current active sessions"""
            active_sessions = [
                session for session in self.current_sessions.values() 
                if session.get('status') in ['playing', 'paused']
            ]
            return jsonify({
                'sessions': active_sessions,
                'count': len(active_sessions),
                'last_updated': datetime.now().isoformat()
            })
        
        @self.app.route('/api/users-devices')
        def api_users_devices():
            """API endpoint for tracked users and devices"""
            tracking_data = self.bridge.get_tracked_users_and_devices()
            # Add persistence info
            tracking_config = self.bridge.config.get('tracking', {})
            tracking_data['persistence_enabled'] = tracking_config.get('enabled', True) and tracking_config.get('auto_save', True)
            tracking_data['persistence_file'] = tracking_config.get('persistence_file', 'tracking_data.json')
            return jsonify(tracking_data)
        
        @self.app.route('/api/users-devices/save', methods=['POST'])
        def api_save_tracking():
            """API endpoint to manually save tracking data"""
            try:
                self.bridge.force_save_tracking_data()
                return jsonify({
                    'success': True,
                    'message': 'Tracking data saved successfully',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/users')
        def api_users():
            """API endpoint for tracked users only"""
            tracking_data = self.bridge.get_tracked_users_and_devices()
            return jsonify({
                'users': tracking_data['users'],
                'count': tracking_data['users_count'],
                'last_updated': datetime.now().isoformat()
            })
        
        @self.app.route('/api/devices')
        def api_devices():
            """API endpoint for tracked devices only"""
            tracking_data = self.bridge.get_tracked_users_and_devices()
            return jsonify({
                'devices': tracking_data['devices'],
                'count': tracking_data['devices_count'],
                'last_updated': datetime.now().isoformat()
            })
        
        @self.app.route('/api/config')
        def api_config():
            """API endpoint for configuration (sanitized)"""
            config_copy = self.bridge.config.copy()
            # Remove sensitive information
            if 'plex' in config_copy:
                config_copy['plex']['token'] = '***HIDDEN***'
            if 'mqtt' in config_copy:
                if 'password' in config_copy['mqtt']:
                    config_copy['mqtt']['password'] = '***HIDDEN***'
            
            return jsonify(config_copy)
    
    def get_uptime(self):
        """Get application uptime"""
        if hasattr(self.bridge, 'start_time'):
            delta = datetime.now() - self.bridge.start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
    
    def update_session(self, music_info, topic):
        """Update current session information for the web interface"""
        session_key = f"{music_info['user']}_{music_info.get('device', 'unknown')}"
        
        session_data = {
            'session_key': session_key,
            'user': music_info.get('user', 'Unknown'),
            'device': music_info.get('device', 'Unknown'),
            'device_original': music_info.get('device_original', 'Unknown'),
            'title': music_info.get('title', ''),
            'artist': music_info.get('artist', ''),
            'album': music_info.get('album', ''),
            'status': music_info.get('status', 'unknown'),
            'progress_percent': music_info.get('progress_percent', 0),
            'duration_formatted': music_info.get('duration_formatted', '0:00'),
            'position_formatted': music_info.get('position_formatted', '0:00'),
            'remaining_formatted': music_info.get('remaining_formatted', '0:00'),
            'thumb': music_info.get('thumb', ''),
            'year': music_info.get('year', ''),
            'track_number': music_info.get('track_number', ''),
            'bitrate': music_info.get('bitrate', ''),
            'codec': music_info.get('codec', ''),
            'topic': topic,
            'last_updated': datetime.now().isoformat()
        }
        
        # Update or add session
        self.current_sessions[session_key] = session_data
    
    def remove_session(self, session_key):
        """Remove a session that's no longer active"""
        if session_key in self.current_sessions:
            del self.current_sessions[session_key]
    
    def clear_inactive_sessions(self, active_session_keys):
        """Remove sessions that are no longer active"""
        inactive_keys = set(self.current_sessions.keys()) - active_session_keys
        for key in inactive_keys:
            self.remove_session(key)
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask web server"""
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)
