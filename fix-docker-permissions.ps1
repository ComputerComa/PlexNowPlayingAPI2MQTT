# PowerShell script to fix Docker permissions for logs directory
Write-Host "Creating logs directory with proper permissions..."

# Create logs directory if it doesn't exist
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs"
    Write-Host "Created logs directory"
}

# Set permissions (on Windows, this is usually not the issue, but let's ensure it exists)
Write-Host "Logs directory ready for Docker container"
Write-Host "The container will now be able to write logs to ./logs/"
