#!/bin/sh
set -e

# Install ffmpeg (if not already installed)
apk add --no-cache ffmpeg


# Start the application using gunicorn
gunicorn --bind=0.0.0.0:80 --timeout 600 app:app