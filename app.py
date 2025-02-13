import os
import glob
import subprocess
from flask import Flask, render_template, request, send_file

# Configure Application
app = Flask(__name__)

# Set the upload and download directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")

app.config["FILE_UPLOADS"] = UPLOADS_DIR

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


@app.route("/")
def home():
    """Home route - Clears old files from uploads and downloads directories."""
    for folder in [UPLOADS_DIR, DOWNLOADS_DIR]:
        for f in glob.glob(os.path.join(folder, '*')):
            os.remove(f)
    return render_template("home.html")


@app.route("/compress", methods=["GET", "POST"])
def compress():
    """Handles file compression using Huffman encoding."""
    if request.method == "GET":
        return render_template("compress.html", check=0)

    # Ensure a file is uploaded
    up_file = request.files.get("file")
    if not up_file or up_file.filename == "":
        return render_template("compress.html", check=-1)

    # Save uploaded file
    filename = up_file.filename
    uploaded_file_path = os.path.join(UPLOADS_DIR, filename)
    up_file.save(uploaded_file_path)

    # Run compression
    compressed_file_path = os.path.join(UPLOADS_DIR, f"{filename}-compressed.bin")
    try:
        subprocess.run(["./huffcompress", uploaded_file_path], check=True)

        if os.path.exists(compressed_file_path):
            subprocess.run(["mv", compressed_file_path, DOWNLOADS_DIR], check=True)
            return render_template("compress.html", check=1)
        else:
            return render_template("compress.html", check=-1)
    except subprocess.CalledProcessError as e:
        print(f"Compression error: {e}")
        return render_template("compress.html", check=-1)


@app.route("/decompress", methods=["GET", "POST"])
def decompress():
    """Handles file decompression using Huffman decoding."""
    if request.method == "GET":
        return render_template("decompress.html", check=0)

    # Ensure a file is uploaded
    up_file = request.files.get("file")
    if not up_file or up_file.filename == "":
        return render_template("decompress.html", check=-1)

    # Save uploaded file
    filename = up_file.filename
    uploaded_file_path = os.path.join(UPLOADS_DIR, filename)
    up_file.save(uploaded_file_path)

    try:
        subprocess.run(["./huffdecompress", uploaded_file_path], check=True)

        # Extract file extension from compressed file
        with open(uploaded_file_path, 'rb') as f:
            ext_length = int.from_bytes(f.read(1), byteorder='big')
            file_ext = f.read(ext_length).decode("utf-8")

        decompressed_filename = f"{filename.split('-')[0]}-decompressed.{file_ext}"
        decompressed_file_path = os.path.join(UPLOADS_DIR, decompressed_filename)

        if os.path.exists(decompressed_file_path):
            subprocess.run(["mv", decompressed_file_path, DOWNLOADS_DIR], check=True)
            return render_template("decompress.html", check=1)
        else:
            return render_template("decompress.html", check=-1)
    except subprocess.CalledProcessError as e:
        print(f"Decompression error: {e}")
        return render_template("decompress.html", check=-1)


@app.route("/download")
def download_file():
    """Allows users to download the processed file."""
    try:
        files = glob.glob(os.path.join(DOWNLOADS_DIR, "*"))
        if not files:
            return "No files available for download", 404
        return send_file(files[0], as_attachment=True)
    except Exception as e:
        print(f"Download error: {e}")
        return "File download failed", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
