import os
import json
import logging
from flask import Flask, request, render_template_string, make_response, session
import csv
from io import StringIO
from fractions import Fraction
import ffmpeg
import uuid  # For generating unique filenames for thumbnails
from flask import send_from_directory

# Set up circular logging
class CircularBufferHandler(logging.Handler):
    def __init__(self, capacity):
        logging.Handler.__init__(self)
        self.capacity = capacity
        self.buffer = []

    def emit(self, record):
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append(self.format(record))

    def get_buffer(self):
        return self.buffer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = CircularBufferHandler(capacity=1000)  # Keep last 1000 log entries
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
app.secret_key = 'ThisIsMySecretKey'  # Make sure to set a secure secret key

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video File Specifications</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #000000;
            --border-color: #ccc;
        }
        .dark-mode {
            --bg-color: #333333;
            --text-color: #ffffff;
            --border-color: #666;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s, color 0.3s;
        }
        .grid-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            padding: 10px;
        }
        .grid-item {
            border: 1px solid var(--border-color);
            padding: 10px;
            text-align: left;
        }
        .file-container {
            display: grid;
            grid-template-columns: 1fr;
            grid-template-rows: repeat(11, auto);
            gap: 5px;
            border: 1px solid var(--border-color);
            padding: 10px;
            margin-bottom: 10px;
        }
        .copy-button {
            margin-top: 10px;
        }
        #darkModeToggle {
            margin-top: 10px;
        }
        #uploadProgressBar, #processingProgressBar {
            width: 100%;
            height: 20px;
            background-color: #ddd;
            margin-top: 10px;
        }
        #uploadProgressBarValue, #processingProgressBarValue {
            width: 0%;
            height: 100%;
            text-align: center;
            line-height: 20px;
            color: white;
        }
        #uploadProgressBarValue {
            background-color: #4CAF50;
        }
        #processingProgressBarValue {
            background-color: #2196F3;
        }
    </style>
</head>
<body>
    <h1>Video File Specifications</h1>
    <input type="file" id="fileInput" multiple>
    <div id="uploadProgressBar">
        <label for="uploadProgressBarValue">File Upload Progress:</label>
        <div id="uploadProgressBarValue">0%</div>
    </div>
    <div id="processingProgressBar">
        <label for="processingProgressBarValue">File Processing Progress:</label>
        <div id="processingProgressBarValue">0%</div>
    </div>
    <div id="results" class="grid-container"></div>
    <button onclick="copyToClipboard()" class="copy-button">Copy to Clipboard</button>
    <button onclick="exportToCSV()" class="copy-button">Export to CSV</button>
    <button id="darkModeToggle" onclick="toggleDarkMode()">Toggle Dark Mode</button>
    <script>
        // Automatically upload files when selected with progress tracking
        document.getElementById('fileInput').addEventListener('change', function () {
            const files = this.files;
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);

            // Update the upload progress bar
            xhr.upload.onprogress = function (event) {
                if (event.lengthComputable) {
                    const percentComplete = Math.round((event.loaded / event.total) * 100);
                    updateProgressBar('uploadProgressBarValue', percentComplete);
                }
            };

            // Handle the response
            xhr.onload = function () {
                if (xhr.status === 200) {
                    const data = JSON.parse(xhr.responseText);
                    updateProgressBar('uploadProgressBarValue', 100); // Set upload progress bar to 100%
                    processFiles(data); // Start processing files
                } else {
                    console.error('Error:', xhr.statusText);
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = `<div class="grid-item">Error: ${xhr.statusText}</div>`;
                }
            };

            // Handle errors
            xhr.onerror = function () {
                console.error('Error during the upload.');
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = `<div class="grid-item">Error during the upload.</div>`;
            };

            // Send the request
            xhr.send(formData);
        });

        function processFiles(data) {
            // Simulate file processing progress
            let percentComplete = 0;
            const interval = setInterval(() => {
                percentComplete += 10; // Increment progress by 10%
                updateProgressBar('processingProgressBarValue', percentComplete);

                if (percentComplete >= 100) {
                    clearInterval(interval); // Stop the interval when progress reaches 100%
                    displayResults(data); // Display the results
                }
            }, 500); // Simulate processing time (adjust as needed)
        }

        function updateProgressBar(progressBarId, percent) {
            const progressBar = document.getElementById(progressBarId);
            progressBar.style.width = percent + '%';
            progressBar.textContent = percent + '%';
        }

        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            data.forEach((file, index) => {
                const fileContainer = document.createElement('div');
                fileContainer.className = 'file-container';

                // Add the thumbnail image
                const thumbnail = document.createElement('img');
                thumbnail.src = `/thumbnails/${file["Thumbnail"]}`;
                thumbnail.alt = `Thumbnail for ${file["File name"]}`;
                thumbnail.style.width = '100px'; // Set thumbnail width
                thumbnail.style.height = 'auto'; // Maintain aspect ratio
                fileContainer.appendChild(thumbnail);

                // Add other file details
                for (const key in file) {
                    if (key !== "Thumbnail") {  // Skip the thumbnail key
                        const div = document.createElement('div');
                        div.className = 'grid-item';
                        div.textContent = `${key}: ${file[key]}`;
                        fileContainer.appendChild(div);
                    }
                }
                resultsDiv.appendChild(fileContainer);
            });
        }

        function copyToClipboard() {
            const resultsDiv = document.getElementById('results');
            const text = resultsDiv.innerText;
            navigator.clipboard.writeText(text);
        }

        function exportToCSV() {
            fetch('/download')
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'video_file_specifications.csv';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                });
        }

        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
        }
    </script>
</body>
</html>
"""

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    file_specs = []
    total_size = 0
    for file in files:
        try:
            file.save(file.filename)
            logger.info(f"Saved file: {file.filename}")
            
            # Generate a unique filename for the thumbnail
            thumbnail_filename = f"thumbnail_{uuid.uuid4().hex}.jpg"
            
            # Extract the first frame using FFmpeg
            ffmpeg.input(file.filename, ss=0).output(thumbnail_filename, vframes=1).run()
            
            # Probe the file with FFmpeg
            probe = ffmpeg.probe(file.filename)
            video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
            audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
            
            if video_streams:
                video_stream = video_streams[0]
                file_spec = {
                    "File name": file.filename,
                    "File size (MB)": round(os.path.getsize(file.filename) / (1024 * 1024), 1),
                    "File type": file.content_type,
                    "Bitrate (MBps)": round(int(video_stream.get('bit_rate', 0)) / (1024 * 1024), 2) if 'bit_rate' in video_stream else 'N/A',
                    "Dimensions": f"{video_stream.get('width', 'N/A')}x{video_stream.get('height', 'N/A')}" if 'width' in video_stream and 'height' in video_stream else 'N/A',
                    "Duration (seconds)": round(float(video_stream.get('duration', 0)), 2) if 'duration' in video_stream else 'N/A',
                    "Frame rate (FPS)": round(float(Fraction(video_stream.get('r_frame_rate', '0/1')))),
                    "Has audio": bool(audio_streams),
                    "Width (pixels)": video_stream.get('width', 'N/A'),
                    "Height (pixels)": video_stream.get('height', 'N/A'),
                    "Thumbnail": thumbnail_filename  # Add thumbnail filename to the file spec
                }
                file_specs.append(file_spec)
                total_size += os.path.getsize(file.filename)
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode('utf-8')}")
            return json.dumps({"error": "Failed to process the video file. Please check the file format."})
        finally:
            os.remove(file.filename)
            if os.path.exists(thumbnail_filename):
                os.remove(thumbnail_filename)

    # Log the session data
    ip_address = request.remote_addr
    num_files = len(files)
    total_size_mb = round(total_size / (1024 * 1024), 1)
    logger.info(f"IP: {ip_address}, Files tested: {num_files}, Total size uploaded: {total_size_mb} MB")

    # Store the file specifications in the session
    session['file_specs'] = json.dumps(file_specs)
    return json.dumps(file_specs)

@app.route('/download')
def download():
    si = StringIO()
    cw = csv.writer(si)
    
    # Write the header
    header = ["File name", "File size (MB)", "File type", "Bitrate (MBps)", "Dimensions", 
              "Duration (seconds)", "Frame rate (FPS)", "Has audio", "Width (pixels)", "Height (pixels)"]
    cw.writerow(header)
    
    # Fetch the data from the session
    file_specs = json.loads(session.get('file_specs', '[]'))
    
    # Write the data rows
    for file_spec in file_specs:
        row = [
            file_spec.get("File name", "N/A"),
            file_spec.get("File size (MB)", "N/A"),
            file_spec.get("File type", "N/A"),
            file_spec.get("Bitrate (MBps)", "N/A"),
            file_spec.get("Dimensions", "N/A"),
            file_spec.get("Duration (seconds)", "N/A"),
            file_spec.get("Frame rate (FPS)", "N/A"),
            file_spec.get("Has audio", "N/A"),
            file_spec.get("Width (pixels)", "N/A"),
            file_spec.get("Height (pixels)", "N/A")
        ]
        cw.writerow(row)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=video_file_specifications.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/thumbnails/<filename>')
def thumbnails(filename):
    return send_from_directory(os.getcwd(), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)