#!/usr/bin/env python3
"""
Helper script to get Last.fm API credentials
This script provides instructions on how to get your Last.fm API key and secret
"""

def print_instructions():
    """Print instructions for getting Last.fm API credentials"""
    print("=" * 60)
    print("Last.fm API Credentials Setup")
    print("=" * 60)
    print()
    print("To enable Last.fm scrobbling in your Plex MQTT Bridge, you need:")
    print("1. Last.fm API Key")
    print("2. Last.fm API Secret")
    print("3. Your Last.fm username")
    print("4. Your Last.fm password")
    print()
    print("Steps to get API credentials:")
    print()
    print("1. Visit: https://www.last.fm/api/account/create")
    print("2. Log in with your Last.fm account")
    print("3. Fill out the application form:")
    print("   - Application name: Plex MQTT Bridge")
    print("   - Application description: Bridge for scrobbling Plex music to Last.fm")
    print("   - Application homepage URL: (leave blank or use your own)")
    print("   - Callback URL: (leave blank)")
    print()
    print("4. After creating the application, you'll get:")
    print("   - API Key (32 characters)")
    print("   - Shared Secret (32 characters)")
    print()
    print("5. Update your config.json file:")
    print('''
{
    ...
    "lastfm": {
        "enabled": true,
        "api_key": "YOUR_API_KEY_HERE",
        "api_secret": "YOUR_API_SECRET_HERE",
        "username": "YOUR_LASTFM_USERNAME",
        "password": "YOUR_LASTFM_PASSWORD",
        "scrobble_threshold": 0.5,
        "min_duration": 30,
        "enhance_metadata": false
    },
    ...
}
''')
    print()
    print("Configuration options:")
    print("- enabled: Enable/disable Last.fm scrobbling")
    print("- scrobble_threshold: Percentage of track that must be played to scrobble (0.5 = 50%)")
    print("- min_duration: Minimum track duration in seconds to be eligible for scrobbling")
    print("- enhance_metadata: Fetch additional metadata from Last.fm (tags, play counts)")
    print("- prevent_duplicates: Enable aggressive duplicate prevention (recommended: true)")
    print()
    print("Environment Variables (alternative to config file):")
    print("- LASTFM_API_KEY: Your Last.fm API key")
    print("- LASTFM_API_SECRET: Your Last.fm API secret")
    print("- LASTFM_USERNAME: Your Last.fm username")
    print("- LASTFM_PASSWORD: Your Last.fm password")
    print()
    print("Troubleshooting:")
    print("- If you see duplicate scrobbles, run: python debug_lastfm.py")
    print("- Test your connection with: python test_lastfm.py")
    print()
    print("Security note:")
    print("- Your Last.fm password is hashed before being sent to Last.fm")
    print("- Consider using environment variables for sensitive data")
    print()
    print("=" * 60)


if __name__ == "__main__":
    print_instructions()
