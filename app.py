import os
import logging
from flask import Flask, request, render_template_string
from werkzeug.utils import secure_filename
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

UPLOAD_FOLDER = '/tmp'  # Temporary directory for uploaded files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# add a debug log to check if the upload folder exists and is writable
print(f"UPLOAD_FOLDER exists: {os.path.exists(app.config['UPLOAD_FOLDER'])}")
print(f"UPLOAD_FOLDER writable: {os.access(app.config['UPLOAD_FOLDER'], os.W_OK)}")



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

    if (files.length === 0) {
        console.error("No files selected");
        alert("Please select a file to upload.");
        return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    console.log("Uploading files:", files);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("Upload successful:", data);
        alert("Upload successful!");
    })
    .catch(error => {
        console.error("Error during upload:", error);
        alert("Error during upload. Check the console for details.");
    });
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
    if 'files' not in request.files:
       return 'No file part', 400

    files = request.files.getlist('files')
    results = []

    for file in files:
        if file.filename == '':
            return 'No selected file', 400

        # Save the file to a temporary directory
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Use the full file path with ffmpeg.probe()
            probe = ffmpeg.probe(file_path)
            results.append(probe)
        except ffmpeg.Error as e:
            logger.error(f"ffprobe error: {e.stderr.decode('utf-8')}")
            return f"ffprobe error: {e.stderr.decode('utf-8')}", 500
        finally:
            # Clean up the temporary file
            os.remove(file_path)

    return {'results': results}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)