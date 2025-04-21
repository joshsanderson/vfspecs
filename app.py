import os
import json
import logging
#from 
# pip install flask ffmpeg
import flask, request, render_template_string, make_response, session
import csv
from io import StringIO
import ffmpeg

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
        #progressBar {
            width: 100%;
            height: 20px;
            background-color: #ddd;
            margin-top: 10px;
        }
        #progressBarValue {
            width: 0%;
            height: 100%;
            background-color: #4CAF50;
            text-align: center;
            line-height: 20px;
            color: white;
        }
    </style>
</head>
<body>
    <h1>Video File Specifications</h1>
    <input type="file" id="fileInput" multiple>
    <button onclick="uploadFiles()">Upload</button>
    <div id="progressBar">
        <div id="progressBarValue">0%</div>
    </div>
    <div id="results" class="grid-container"></div>
    <button onclick="copyToClipboard()" class="copy-button">Copy to Clipboard</button>
    <button onclick="exportToCSV()" class="copy-button">Export to CSV</button>
    <button id="darkModeToggle" onclick="toggleDarkMode()">Toggle Dark Mode</button>
    <script>
        function uploadFiles() {
            const input = document.getElementById('fileInput');
            const files = input.files;
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response;
            })
            .then(response => {
                const reader = response.body.getReader();
                return new ReadableStream({
                    start(controller) {
                        return pump();
                        function pump() {
                            return reader.read().then(({ done, value }) => {
                                if (done) {
                                    controller.close();
                                    return;
                                }
                                controller.enqueue(value);
                                return pump();
                            });
                        }
                    }
                });
            })
            .then(stream => new Response(stream))
            .then(response => response.json())
            .then(data => {
                displayResults(data);
                updateProgressBar(100);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            data.forEach((file, index) => {
                const fileContainer = document.createElement('div');
                fileContainer.className = 'file-container';
                for (const key in file) {
                    const div = document.createElement('div');
                    div.className = 'grid-item';
                    div.textContent = `${key}: ${file[key]}`;
                    fileContainer.appendChild(div);
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
        function updateProgressBar(percent) {
            const progressBar = document.getElementById('progressBarValue');
            progressBar.style.width = percent + '%';
            progressBar.textContent = percent + '%';
        }
        // Function to handle the progress event
        function handleProgress(event) {
            if (event.lengthComputable) {
                const percent = Math.round((event.loaded / event.total) * 100);
                updateProgressBar(percent);
            }
        }
        // Add event listener for upload progress
        document.getElementById('fileInput').addEventListener('change', function() {
            const files = this.files;
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            const xhr = new XMLHttpRequest();
            xhr.upload.addEventListener('progress', handleProgress, false);
            xhr.open('POST', '/upload', true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    const data = JSON.parse(xhr.responseText);
                    displayResults(data);
                } else {
                    console.error('Error uploading files');
                }
            };
            xhr.send(formData);
        });
        // Initialize dark mode toggle based on system preference
        
    // Check and apply dark mode preference on page load
    document.addEventListener('DOMContentLoaded', () => {
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
        }
    });

    // Update toggleDarkMode function
    function toggleDarkMode() {
        const isDarkMode = document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
    }

    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    file_specs = []
    total_size = 0
    for file in files:
        file.save(file.filename)
        probe = ffmpeg.probe(file.filename)
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        if video_streams:
            # Select the first video stream
            video_stream = video_streams[0]
            file_spec = {
                "File name": file.filename,
                "File size (MB)": round(os.path.getsize(file.filename) / (1024 * 1024), 1),
                "File type": file.content_type,
                "Bitrate (MBps)": round(int(video_stream.get('bit_rate', 0)) / (1024 * 1024), 2) if 'bit_rate' in video_stream else 'N/A',
                "Dimensions": f"{video_stream.get('width', 'N/A')}x{video_stream.get('height', 'N/A')}" if 'width' in video_stream and 'height' in video_stream else 'N/A',
                "Duration (seconds)": round(float(video_stream.get('duration', 0)), 2) if 'duration' in video_stream else 'N/A',
                "Frame rate (FPS)": round(eval(video_stream.get('r_frame_rate', '0/1'))) if 'r_frame_rate' in video_stream else 'N/A',
                "Has audio": bool(audio_streams),
                "Width (pixels)": video_stream.get('width', 'N/A'),
                "Height (pixels)": video_stream.get('height', 'N/A')
            }
            file_specs.append(file_spec)
            total_size += os.path.getsize(file.filename)
        os.remove(file.filename)
    
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
            file_spec["File name"],
            file_spec["File size (MB)"],
            file_spec["File type"],
            file_spec["Bitrate (MBps)"],
            file_spec["Dimensions"],
            file_spec["Duration (seconds)"],
            file_spec["Frame rate (FPS)"],
            file_spec["Has audio"],
            file_spec["Width (pixels)"],
            file_spec["Height (pixels)"]
        ]
        cw.writerow(row)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=video_file_specifications.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    app.run(debug=True)