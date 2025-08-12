#!/bin/bash
# Script to fix Docker permissions for logs directory

echo "Creating logs directory with proper permissions..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Set proper ownership (UID 1000 is typically the first user created in container)
# This allows the container's app user to write to the logs directory
sudo chown -R 1000:1000 logs

echo "Logs directory permissions fixed"
echo "The container will now be able to write logs to ./logs/"
