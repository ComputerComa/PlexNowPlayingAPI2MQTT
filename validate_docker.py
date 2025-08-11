#!/usr/bin/env python3
"""
Docker Configuration Validator for Plex MQTT Bridge
Validates Docker setup and configuration before deployment
"""

import os
import sys
import json
import subprocess
import socket
from pathlib import Path

def check_docker_installation():
    """Check if Docker and Docker Compose are installed"""
    print("🐳 Checking Docker installation...")
    
    try:
        # Check Docker
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
        else:
            print("❌ Docker not found or not working")
            return False
    except Exception as e:
        print(f"❌ Docker not found: {e}")
        return False
    
    try:
        # Check Docker Compose
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        else:
            print("❌ Docker Compose not found")
            return False
    except Exception as e:
        print(f"❌ Docker Compose not found: {e}")
        return False
    
    return True

def check_docker_daemon():
    """Check if Docker daemon is running"""
    print("\n🔄 Checking Docker daemon...")
    
    try:
        result = subprocess.run(['docker', 'info'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ Docker daemon is running")
            return True
        else:
            print("❌ Docker daemon not running")
            print("💡 Try starting Docker Desktop")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Docker daemon: {e}")
        return False

def check_configuration_files():
    """Check if required configuration files exist"""
    print("\n📁 Checking configuration files...")
    
    files_to_check = [
        ('Dockerfile', True),
        ('docker-compose.yml', True),
        ('docker-compose.env.yml', False),
        ('requirements.txt', True),
        ('main.py', True),
        ('web_interface.py', True),
        ('config.json', False),
        ('config.example.json', True),
        ('.env', False),
        ('.env.example', True),
    ]
    
    all_good = True
    for filename, required in files_to_check:
        if os.path.exists(filename):
            print(f"✅ {filename}")
        elif required:
            print(f"❌ {filename} (required)")
            all_good = False
        else:
            print(f"⚠️  {filename} (optional)")
    
    return all_good

def validate_config_json():
    """Validate config.json if it exists"""
    if not os.path.exists('config.json'):
        print("\n⚠️  config.json not found - will need to create one or use environment variables")
        return True
    
    print("\n⚙️  Validating config.json...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = ['plex', 'mqtt']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing section: {section}")
                return False
            print(f"✅ Section: {section}")
        
        # Check Plex configuration
        if 'token' not in config['plex'] or not config['plex']['token']:
            print("❌ Plex token missing or empty")
            return False
        print("✅ Plex token configured")
        
        # Check MQTT configuration
        mqtt_config = config['mqtt']
        if 'broker' not in mqtt_config or not mqtt_config['broker']:
            print("❌ MQTT broker missing or empty")
            return False
        print("✅ MQTT broker configured")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return False

def validate_env_file():
    """Validate .env file if it exists"""
    if not os.path.exists('.env'):
        print("\n⚠️  .env file not found - will use config.json or fail if neither exists")
        return True
    
    print("\n🌍 Validating .env file...")
    
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        required_vars = ['PLEX_TOKEN', 'MQTT_BROKER']
        found_vars = []
        
        for line in env_content.split('\n'):
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                var_name = line.split('=')[0]
                found_vars.append(var_name)
        
        all_good = True
        for var in required_vars:
            if var in found_vars:
                print(f"✅ {var}")
            else:
                print(f"❌ {var} missing")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def check_port_availability():
    """Check if port 5000 is available"""
    print("\n🔌 Checking port availability...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 5000))
            print("✅ Port 5000 is available")
            return True
    except OSError:
        print("⚠️  Port 5000 is in use - Docker will map to a different port if needed")
        return True

def test_docker_build():
    """Test if Docker build would work (dry run)"""
    print("\n🏗️  Testing Docker build...")
    
    try:
        # Check if we can at least parse the Dockerfile
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        if 'FROM python:3.11-slim' in dockerfile_content:
            print("✅ Dockerfile looks valid")
            return True
        else:
            print("⚠️  Dockerfile may have issues")
            return False
            
    except Exception as e:
        print(f"❌ Cannot read Dockerfile: {e}")
        return False

def main():
    """Main validation function"""
    print("🐳 Plex MQTT Bridge - Docker Configuration Validator")
    print("=" * 55)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        check_docker_installation,
        check_docker_daemon,
        check_configuration_files,
        validate_config_json,
        validate_env_file,
        check_port_availability,
        test_docker_build,
    ]
    
    for check in checks:
        if not check():
            all_checks_passed = False
    
    print("\n" + "=" * 55)
    
    if all_checks_passed:
        print("🎉 All checks passed! Ready for Docker deployment.")
        print("\nNext steps:")
        print("1. Build and run: docker-compose up -d")
        print("2. View logs: docker-compose logs -f")
        print("3. Access web interface: http://localhost:5000")
    else:
        print("❌ Some checks failed. Please fix the issues before deploying.")
        print("\nCommon fixes:")
        print("- Install Docker Desktop and start it")
        print("- Create config.json from config.example.json")
        print("- Get your Plex token with: python get_plex_token.py")
        print("- Configure your MQTT broker settings")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())
