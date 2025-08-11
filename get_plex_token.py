#!/usr/bin/env python3
"""
Utility script to help get Plex authentication token using PlexAPI
"""

import getpass
import sys
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import BadRequest, Unauthorized


def get_plex_token():
    """Get Plex authentication token using PlexAPI"""
    print("Plex Token Generator")
    print("===================")
    print("This will generate a token for your Plex account.")
    print("Your credentials are only used to authenticate with Plex.tv")
    print()
    
    username = input("Enter your Plex username or email: ")
    password = getpass.getpass("Enter your Plex password: ")
    
    try:
        # Authenticate with MyPlex
        account = MyPlexAccount(username, password)
        
        print(f"\nSuccess! Authenticated as: {account.username}")
        print(f"Account ID: {account.id}")
        print(f"Email: {account.email}")
        
        # Get the authentication token
        token = account.authenticationToken
        
        print(f"\nYour Plex token is:")
        print(f"{token}")
        print(f"\nAdd this token to your config.json file:")
        print(f'"token": "{token}"')
        
        # Optional: List available servers
        print(f"\nAvailable Plex servers on your account:")
        for resource in account.resources():
            if resource.product == 'Plex Media Server':
                print(f"  - {resource.name}: {resource.connections[0].uri if resource.connections else 'No connections'}")
        
        return token
        
    except Unauthorized:
        print("Error: Invalid username or password")
        return None
    except BadRequest as e:
        print(f"Error: Bad request - {e}")
        return None
    except Exception as e:
        print(f"Error authenticating with Plex: {e}")
        return None


def test_token():
    """Test an existing token"""
    print("\nPlex Token Tester")
    print("=================")
    
    token = input("Enter your Plex token to test: ").strip()
    
    if not token:
        print("No token provided")
        return False
    
    try:
        # Test the token
        account = MyPlexAccount(token=token)
        print(f"Success! Token is valid for account: {account.username}")
        
        # List servers
        print(f"\nAvailable servers:")
        for resource in account.resources():
            if resource.product == 'Plex Media Server':
                print(f"  - {resource.name}: {resource.connections[0].uri if resource.connections else 'No connections'}")
        
        return True
        
    except Unauthorized:
        print("Error: Invalid token")
        return False
    except Exception as e:
        print(f"Error testing token: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_token()
    else:
        get_plex_token()
        
        # Ask if they want to test the token
        test = input("\nWould you like to test the token? (y/n): ").lower().strip()
        if test in ['y', 'yes']:
            test_token()
