#!/bin/bash
set -e

# Install ffmpeg (if not already installed)
apt-get update && apt-get install -y ffmpeg


# Start the application using gunicorn
gunicorn --bind=0.0.0.0:80 --timeout 600 app:app
