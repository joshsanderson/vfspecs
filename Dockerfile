FROM python:3.13-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 80

# Run the app
#CMD ["python", "app.py"]
CMD ["gunicorn", "-b", "0.0.0.0:80", "app:app"]