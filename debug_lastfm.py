#!/usr/bin/env python3
"""
Debug script for Last.fm scrobbling issues
This script helps debug and clean up Last.fm scrobbling problems
"""

import json
import os
import sys
from datetime import datetime, timedelta
import time

try:
    import pylast
except ImportError:
    print("❌ pylast library not found. Install with: pip install pylast")
    sys.exit(1)


def analyze_lastfm_scrobbles():
    """Analyze recent Last.fm scrobbles for duplicates"""
    print("🔍 Last.fm Scrobble Analysis")
    print("=" * 50)
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please create it from config.example.json")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False
    
    lastfm_config = config.get('lastfm', {})
    
    if not lastfm_config.get('enabled', False):
        print("❌ Last.fm is disabled in config.json")
        return False
    
    # Get credentials (support environment variables)
    api_key = lastfm_config.get('api_key', '') or os.getenv('LASTFM_API_KEY', '')
    api_secret = lastfm_config.get('api_secret', '') or os.getenv('LASTFM_API_SECRET', '')
    username = lastfm_config.get('username', '') or os.getenv('LASTFM_USERNAME', '')
    password = lastfm_config.get('password', '') or os.getenv('LASTFM_PASSWORD', '')
    
    if not all([api_key, api_secret, username, password]):
        print("❌ Missing Last.fm credentials. Check config.json or environment variables.")
        return False
    
    try:
        # Initialize Last.fm network
        network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret,
            username=username,
            password_hash=pylast.md5(password)
        )
        
        user = network.get_user(username)
        
        print(f"📊 Analyzing recent scrobbles for: {username}")
        
        # Get recent tracks (last 50)
        recent_tracks = user.get_recent_tracks(limit=50)
        
        if not recent_tracks:
            print("🎵 No recent tracks found")
            return True
        
        print(f"📈 Found {len(recent_tracks)} recent tracks")
        print()
        
        # Analyze for duplicates
        track_counts = {}
        recent_duplicates = []
        
        for track in recent_tracks:
            track_key = f"{track.track.artist} - {track.track.title}"
            timestamp = track.timestamp
            
            if track_key not in track_counts:
                track_counts[track_key] = []
            
            track_counts[track_key].append({
                'timestamp': timestamp,
                'time_str': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'Now Playing'
            })
        
        # Find duplicates within a short time window (5 minutes)
        for track_key, plays in track_counts.items():
            if len(plays) > 1:
                # Sort by timestamp
                plays.sort(key=lambda x: x['timestamp'] or time.time())
                
                # Check for plays within 5 minutes of each other
                for i in range(1, len(plays)):
                    if plays[i]['timestamp'] and plays[i-1]['timestamp']:
                        time_diff = plays[i]['timestamp'] - plays[i-1]['timestamp']
                        if time_diff < 300:  # 5 minutes
                            recent_duplicates.append({
                                'track': track_key,
                                'time_diff': time_diff,
                                'timestamps': [plays[i-1]['time_str'], plays[i]['time_str']]
                            })
        
        if recent_duplicates:
            print("⚠️  Potential duplicate scrobbles found:")
            print()
            for dup in recent_duplicates:
                print(f"🎵 {dup['track']}")
                print(f"   Times: {dup['timestamps'][0]} → {dup['timestamps'][1]}")
                print(f"   Gap: {dup['time_diff']} seconds")
                print()
        else:
            print("✅ No duplicate scrobbles found in recent tracks!")
        
        # Show current tracking data from persistence
        print("\n📁 Current tracking data:")
        tracking_file = config.get('tracking', {}).get('persistence_file', 'tracking_data.json')
        
        try:
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
            
            if 'scrobbled_tracks' in tracking_data:
                scrobbled_count = len(tracking_data['scrobbled_tracks'])
                print(f"   Tracked scrobbles: {scrobbled_count}")
                
                # Show most recent scrobbles from tracking
                if scrobbled_count > 0:
                    print("   Most recent tracked scrobbles:")
                    sorted_scrobbles = sorted(
                        tracking_data['scrobbled_tracks'].items(),
                        key=lambda x: x[1]['timestamp'] if isinstance(x[1], dict) else x[1],
                        reverse=True
                    )[:5]
                    
                    for pid, data in sorted_scrobbles:
                        if isinstance(data, dict):
                            track_name = f"{data.get('artist', '?')} - {data.get('title', '?')}"
                            timestamp = data.get('timestamp', 0)
                        else:
                            track_name = pid.split(':')[0:2]  # Extract from playback_id
                            timestamp = data
                        
                        time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"     {track_name} at {time_str}")
            else:
                print("   No scrobble tracking data found")
                
        except FileNotFoundError:
            print(f"   No tracking file found: {tracking_file}")
        except Exception as e:
            print(f"   Error reading tracking file: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing scrobbles: {e}")
        return False


def clear_scrobble_tracking():
    """Clear the local scrobble tracking data"""
    print("🧹 Clearing local scrobble tracking data...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    
    tracking_file = config.get('tracking', {}).get('persistence_file', 'tracking_data.json')
    
    try:
        with open(tracking_file, 'r') as f:
            data = json.load(f)
        
        if 'scrobbled_tracks' in data:
            del data['scrobbled_tracks']
            
            with open(tracking_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Cleared scrobble tracking data from {tracking_file}")
            print("   This will allow the app to start fresh with duplicate prevention")
            return True
        else:
            print("   No scrobble tracking data found to clear")
            return True
            
    except FileNotFoundError:
        print(f"   No tracking file found: {tracking_file}")
        return True
    except Exception as e:
        print(f"❌ Error clearing tracking data: {e}")
        return False


def main():
    """Main function"""
    print("🎵 Last.fm Scrobble Debugger")
    print("=" * 40)
    print()
    print("Choose an option:")
    print("1. Analyze recent scrobbles for duplicates")
    print("2. Clear local scrobble tracking data")
    print("3. Exit")
    print()
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            print()
            analyze_lastfm_scrobbles()
        elif choice == '2':
            print()
            confirm = input("Are you sure you want to clear scrobble tracking? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                clear_scrobble_tracking()
            else:
                print("Cancelled")
        elif choice == '3':
            print("Goodbye!")
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
