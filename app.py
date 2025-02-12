import os
import time
import glob
from flask import Flask, redirect, render_template, request, send_file

# Configure Application
app = Flask(__name__)
global filename
global ftype

@app.route("/")
def home():
    # Delete old files
    filelist = glob.glob('uploads/*')
    for f in filelist:
        os.remove(f)
    filelist = glob.glob('downloads/*')
    for f in filelist:
        os.remove(f)
    return render_template("home.html")

# Set the upload and download directories
UPLOADS_DIR = r"uploads"
DOWNLOADS_DIR = r"downloads"

app.config["FILE_UPLOADS"] = UPLOADS_DIR

@app.route("/compress", methods=["GET", "POST"])
def compress():
    if request.method == "GET":
        return render_template("compress.html", check=0)
    else:
        up_file = request.files["file"]
        if len(up_file.filename) > 0:
            global filename
            global ftype
            filename = up_file.filename
            print(f"Uploaded file: {filename}")
            
            # Save the uploaded file to the uploads directory
            up_file.save(os.path.join(app.config["FILE_UPLOADS"], filename))
            
            # Run the compression executable
            print("Running compression...")
            os.system(r'huffcompress.exe ' + 
                      os.path.join(UPLOADS_DIR, filename))
            
            # Extract the base name of the file (without extension)
            filename = filename[:filename.index(".", 1)]
            ftype = "-compressed.bin"
            
            # Check if the compressed file exists in the uploads directory
            compressed_file_path = os.path.join(UPLOADS_DIR, f'{filename}{ftype}')
            if os.path.exists(compressed_file_path):
                print(f"Compressed file found: {compressed_file_path}")
                
                # Move the compressed file to the downloads directory
                os.system(f'move "{compressed_file_path}" "{DOWNLOADS_DIR}"')
                print(f"Moved {compressed_file_path} to {DOWNLOADS_DIR}")
            else:
                print(f"Error: Compressed file not found at {compressed_file_path}")
                return render_template("compress.html", check=-1)
            
            return render_template("compress.html", check=1)
        else:
            print("ERROR: No file uploaded")
            return render_template("compress.html", check=-1)

@app.route("/decompress", methods=["GET", "POST"])
def decompress():
    if request.method == "GET":
        return render_template("decompress.html", check=0)
    else:
        up_file = request.files["file"]
        if len(up_file.filename) > 0:
            global filename
            global ftype
            filename = up_file.filename
            print(f"Uploaded file: {filename}")
            
            # Save the uploaded file to the uploads directory
            up_file.save(os.path.join(app.config["FILE_UPLOADS"], filename))
            
            # Run the decompression executable
            print("Running decompression...")
            os.system(r'huffdecompress.exe ' + 
                      os.path.join(UPLOADS_DIR, filename))
            
            # Open the file to read the original file extension
            f = open(os.path.join(UPLOADS_DIR, filename), 'rb')
            ftype = "-decompressed." + (f.read(int(f.read(1)))).decode("utf-8")
            f.close()
            
            # Extract the base name of the file (without extension)
            filename = filename[:filename.index("-", 1)]
            
            # Check if the decompressed file exists in the uploads directory
            decompressed_file_path = os.path.join(UPLOADS_DIR, f'{filename}{ftype}')
            if os.path.exists(decompressed_file_path):
                print(f"Decompressed file found: {decompressed_file_path}")
                
                # Move the decompressed file to the downloads directory
                os.system(f'move "{decompressed_file_path}" "{DOWNLOADS_DIR}"')
                print(f"Moved {decompressed_file_path} to {DOWNLOADS_DIR}")
            else:
                print(f"Error: Decompressed file not found at {decompressed_file_path}")
                return render_template("decompress.html", check=-1)
            
            return render_template("decompress.html", check=1)
        else:
            print("ERROR: No file uploaded")
            return render_template("decompress.html", check=-1)

@app.route("/download")
def download_file():
    global filename
    global ftype
    # Construct the full path to the file in the downloads directory
    path = os.path.join(DOWNLOADS_DIR, f'{filename}{ftype}')
    
    # Check if the file exists before attempting to send it
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        print(f"Error: File not found at {path}")
        return "File not found", 404

# Restart application whenever changes are made
if __name__ == "__main__":
    app.run(debug=True)
