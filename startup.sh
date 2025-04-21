# filepath: /Users/josh.sanderson/Library/CloudStorage/OneDrive-Vizio,Inc/DevProjects/VideoFileSpecifications/vfspecs/startup.sh


#!/bin/bash
set -e

# Install ffmpeg (if not already installed)
apt-get update && apt-get install -y ffmpeg

# Start the application using gunicorn
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app





#apt-get update
#apt-get install -y ffmpeg
#python3 app.py
#gunicorn --bind=0.0.0:80 --timeout=600 --workers=4 app:app


# This script updates the package list, installs ffmpeg, and then runs the Python application.
# Ensure this script has execute permissions:
# chmod +x startup.sh
# To run this script, use the command:
# ./startup.sh
# Note: This script is intended for a Debian-based system. Adjust package manager commands as necessary for other distributions.
# If you need to run this script in a Docker container, ensure the Dockerfile includes this script and sets it as the entrypoint or command.

# If you are using a virtual environment, make sure to activate it before running the Python application.
# Example for activating a virtual environment:
# source /path/to/your/venv/bin/activate
# If you want to run this script in a Docker container, you can create a Dockerfile like this:
# FROM python:3.9-slim
# COPY startup.sh /usr/local/bin/startup.sh
# RUN chmod +x /usr/local/bin/startup.sh
# ENTRYPOINT ["/usr/local/bin/startup.sh"]
# If you need to run this script in a different environment, ensure that the necessary dependencies are installed.
# If you are using a different package manager, adjust the installation command accordingly.
# Example for Red Hat-based systems:
# yum install -y ffmpeg
# Example for Alpine Linux:
# apk add ffmpeg
# If you encounter any issues, check the logs for errors and ensure that all dependencies are correctly installed.
# If you want to run this script in a specific Python environment, you can specify the Python interpreter:
# /path/to/your/python3 app.py
# If you need to run this script with specific environment variables, you can set them before running the script:
# export VARIABLE_NAME=value
# ./startup.sh
