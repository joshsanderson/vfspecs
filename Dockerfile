FROM python:3.10-slim-bullseye

COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh
ENTRYPOINT ["/usr/local/bin/startup.sh"]

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg 
#build-essential
RUN mkdir -p /tmp && chmod 777 /tmp
# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 80

# Run the app
CMD ["gunicorn", "-b", "0.0.0.0:80", "app:app"]