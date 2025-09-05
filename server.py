from flask import Flask, request, send_file
import os

app = Flask(__name__)
SCRIPT_FILE = "script.lua"

# Serve the script
@app.route("/script.lua", methods=["GET"])
def get_script():
    if os.path.exists(SCRIPT_FILE):
        return send_file(SCRIPT_FILE, mimetype="text/plain")
    return "No script uploaded yet.", 404

# Upload a new script
@app.route("/upload", methods=["POST"])
def upload_script():
    if "file" not in request.files:
        return "No file uploaded.", 400
    
    file = request.files["file"]
    if file.filename == "":
        return "Empty filename.", 400

    file.save(SCRIPT_FILE)
    return "Script uploaded successfully!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
