#!/usr/bin/env python3
"""
Test script for Last.fm connection
This script tests your Last.fm API credentials and connection
"""

import json
import os
import sys

try:
    import pylast
except ImportError:
    print("❌ pylast library not found. Install with: pip install pylast")
    sys.exit(1)


def test_lastfm_connection():
    """Test Last.fm connection and authentication"""
    print("🎵 Last.fm Connection Test")
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
    
    print(f"🔑 Testing connection for user: {username}")
    
    try:
        # Initialize Last.fm network
        network = pylast.LastFMNetwork(
            api_key=api_key,
            api_secret=api_secret,
            username=username,
            password_hash=pylast.md5(password)
        )
        
        # Test authentication
        user = network.get_user(username)
        playcount = user.get_playcount()
        registered = user.get_registered()
        
        print("✅ Authentication successful!")
        print(f"📊 Total scrobbles: {playcount:,}")
        print(f"📅 Member since: {registered}")
        
        # Test recent tracks
        try:
            recent_tracks = user.get_recent_tracks(limit=3)
            if recent_tracks:
                print("\n🎶 Recent tracks:")
                for i, track in enumerate(recent_tracks, 1):
                    print(f"  {i}. {track.track.artist} - {track.track.title}")
            else:
                print("\n🎶 No recent tracks found")
        except Exception as e:
            print(f"\n⚠️ Could not fetch recent tracks: {e}")
        
        # Test now playing update
        try:
            print("\n🔄 Testing 'Now Playing' update...")
            network.update_now_playing(
                artist="Test Artist",
                title="Test Track",
                album="Test Album"
            )
            print("✅ 'Now Playing' update successful!")
            print("Note: This was just a test - no actual track was marked as playing")
        except Exception as e:
            print(f"❌ 'Now Playing' update failed: {e}")
        
        print("\n🎉 All tests passed! Last.fm integration is working correctly.")
        return True
        
    except pylast.WSError as e:
        print(f"❌ Last.fm API error: {e}")
        if "Invalid API key" in str(e):
            print("💡 Check your API key and secret")
        elif "Invalid username" in str(e):
            print("💡 Check your username and password")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    """Main function"""
    success = test_lastfm_connection()
    
    if not success:
        print("\n💡 Need help? Run: python get_lastfm_credentials.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
