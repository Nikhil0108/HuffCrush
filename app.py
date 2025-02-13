import os
import glob
import shutil
import subprocess
from flask import Flask, render_template, request, send_file, session
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session storage

# Define directories
UPLOADS_DIR = "uploads"
DOWNLOADS_DIR = "downloads"
COMPRESSOR_EXEC = "./huffcompress"  # Use "./huffcompress" for Linux/macOS
DECOMPRESSOR_EXEC = "./huffdecompress"

# Ensure upload and download directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

@app.route("/")
def home():
    """Clears old files and renders home page."""
    for folder in [UPLOADS_DIR, DOWNLOADS_DIR]:
        filelist = glob.glob(os.path.join(folder, "*"))
        for f in filelist:
            os.remove(f)
    return render_template("home.html")

@app.route("/compress", methods=["GET", "POST"])
def compress():
    if request.method == "GET":
        return render_template("compress.html", check=0)
    else:
        up_file = request.files["file"]
        if up_file and up_file.filename:
            filename = secure_filename(up_file.filename)
            filepath = os.path.join(UPLOADS_DIR, filename)
            up_file.save(filepath)

            print(f"✅ Uploaded file: {filename}")

            # Run compression executable
            print("🔹 Running compression...")
            result = subprocess.run([COMPRESSOR_EXEC, filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("📝 Compression Output:", result.stdout)
            print("❗ Compression Error:", result.stderr)

            # Check if compressed file exists
            compressed_filename = f"{filename.rsplit('.', 1)[0]}-compressed.bin"
            compressed_filepath = os.path.join(UPLOADS_DIR, compressed_filename)

            print("📂 Files in upload directory:", os.listdir(UPLOADS_DIR))

            if os.path.exists(compressed_filepath):
                print(f"✅ Compressed file found: {compressed_filepath}")
                shutil.move(compressed_filepath, os.path.join(DOWNLOADS_DIR, compressed_filename))
                session["filename"] = compressed_filename
                return render_template("compress.html", check=1)
            else:
                print("❌ ERROR: Compressed file not found")
                return render_template("compress.html", check=-1)
        else:
            print("❌ ERROR: No file uploaded")
            return render_template("compress.html", check=-1)

@app.route("/decompress", methods=["GET", "POST"])
def decompress():
    if request.method == "GET":
        return render_template("decompress.html", check=0)
    else:
        up_file = request.files["file"]
        if up_file and up_file.filename:
            filename = secure_filename(up_file.filename)
            filepath = os.path.join(UPLOADS_DIR, filename)
            up_file.save(filepath)

            print(f"✅ Uploaded file: {filename}")

            # Run decompression executable
            print("🔹 Running decompression...")
            result = subprocess.run([DECOMPRESSOR_EXEC, filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            print("📝 Decompression Output:", result.stdout)
            print("❗ Decompression Error:", result.stderr)

            # Determine decompressed filename
            with open(filepath, 'rb') as f:
                ext_length = int(f.read(1))
                ftype = f.read(ext_length).decode("utf-8")
            
            decompressed_filename = f"{filename.rsplit('-', 1)[0]}-decompressed.{ftype}"
            decompressed_filepath = os.path.join(UPLOADS_DIR, decompressed_filename)

            print("📂 Files in upload directory:", os.listdir(UPLOADS_DIR))

            if os.path.exists(decompressed_filepath):
                print(f"✅ Decompressed file found: {decompressed_filepath}")
                shutil.move(decompressed_filepath, os.path.join(DOWNLOADS_DIR, decompressed_filename))
                session["filename"] = decompressed_filename
                return render_template("decompress.html", check=1)
            else:
                print("❌ ERROR: Decompressed file not found")
                return render_template("decompress.html", check=-1)
        else:
            print("❌ ERROR: No file uploaded")
            return render_template("decompress.html", check=-1)

@app.route("/download")
def download_file():
    """Serves the compressed or decompressed file for download."""
    filename = session.get("filename")
    if not filename:
        return "No file available for download", 404

    path = os.path.join(DOWNLOADS_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        print(f"❌ ERROR: File not found at {path}")
        return "File not found", 404

if __name__ == "__main__":
    app.run(debug=True)
