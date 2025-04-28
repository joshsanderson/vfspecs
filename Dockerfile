FROM python:3.13-alpine3.21

COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh
ENTRYPOINT ["/usr/local/bin/startup.sh"]

# Install ffmpeg
RUN apk add --no-cache ffmpeg

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
CMD ["gunicorn", "-b", "0.0.0.0:80", "--workers", "4", "app:app"]