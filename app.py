import os
import glob
import shutil
import subprocess
from flask import Flask, render_template, request, send_file, session
from werkzeug.utils import secure_filename

# Configure Application
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Set upload and download directories
UPLOADS_DIR = "uploads"
DOWNLOADS_DIR = "downloads"

# Ensure directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

@app.route("/")
def home():
    # Delete old files
    for f in glob.glob(f"{UPLOADS_DIR}/*"):
        os.remove(f)
    for f in glob.glob(f"{DOWNLOADS_DIR}/*"):
        os.remove(f)
    return render_template("home.html")

@app.route("/compress", methods=["GET", "POST"])
def compress():
    if request.method == "GET":
        return render_template("compress.html", check=0)
    
    up_file = request.files["file"]
    if up_file.filename:
        filename = secure_filename(up_file.filename)
        file_path = os.path.join(UPLOADS_DIR, filename)
        up_file.save(file_path)

        # Run compression
        compressed_file = os.path.join(UPLOADS_DIR, f"{filename}-compressed.bin")
        subprocess.run(["./huffcompress", file_path])

        if os.path.exists(compressed_file):
            shutil.move(compressed_file, DOWNLOADS_DIR)
            session["filename"] = filename
            session["ftype"] = "-compressed.bin"
            return render_template("compress.html", check=1)
        else:
            return render_template("compress.html", check=-1)
    return render_template("compress.html", check=-1)

@app.route("/decompress", methods=["GET", "POST"])
def decompress():
    if request.method == "GET":
        return render_template("decompress.html", check=0)
    
    up_file = request.files["file"]
    if up_file.filename:
        filename = secure_filename(up_file.filename)
        file_path = os.path.join(UPLOADS_DIR, filename)
        up_file.save(file_path)

        # Run decompression
        subprocess.run(["./huffdecompress", file_path])

        # Read original file extension
        with open(file_path, "rb") as f:
            ext_length = int(f.read(1))
            ftype = "-decompressed." + f.read(ext_length).decode("utf-8")

        decompressed_file = os.path.join(UPLOADS_DIR, f"{filename.split('-')[0]}{ftype}")

        if os.path.exists(decompressed_file):
            shutil.move(decompressed_file, DOWNLOADS_DIR)
            session["filename"] = filename.split("-")[0]
            session["ftype"] = ftype
            return render_template("decompress.html", check=1)
        else:
            return render_template("decompress.html", check=-1)
    return render_template("decompress.html", check=-1)

@app.route("/download")
def download_file():
    filename = session.get("filename")
    ftype = session.get("ftype")
    if not filename or not ftype:
        return "File not found", 404

    path = os.path.join(DOWNLOADS_DIR, f"{filename}{ftype}")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
