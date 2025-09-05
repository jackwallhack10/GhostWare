import os
from flask import Flask, request, send_file, render_template_string, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "changeme")  # Needed for flashing messages

SCRIPT_FILE = "script.lua"
UPLOAD_KEY = os.environ.get("UPLOAD_KEY", "changeme")  # Optional password for web upload

# Serve the Lua script
@app.route("/script.lua", methods=["GET"])
def get_script():
    if os.path.exists(SCRIPT_FILE):
        return send_file(SCRIPT_FILE, mimetype="text/plain")
    return "No script uploaded yet.", 404

# Web upload page
@app.route("/", methods=["GET", "POST"])
def upload_page():
    message = None
    filename = None
    filesize = None

    if request.method == "POST":
        # Optional password check
        password = request.form.get("password", "")
        if password != UPLOAD_KEY:
            flash("Unauthorized: Wrong password!", "error")
            return redirect(url_for("upload_page"))

        if "file" not in request.files:
            flash("No file selected.", "error")
            return redirect(url_for("upload_page"))

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(url_for("upload_page"))

        # Save temporarily
        temp_path = "temp_uploaded.lua"
        file.save(temp_path)

        filename = file.filename
        filesize = os.path.getsize(temp_path)
        message = f"Uploaded '{filename}' ({filesize} bytes). Click Save to finalize."

        # Store info in session for saving
        request.environ["uploaded_file"] = temp_path

    # HTML template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lua Script Upload</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 50px; }}
            .message {{ margin-top: 20px; color: green; }}
            .error {{ color: red; }}
            button {{ margin-top: 10px; padding: 5px 15px; }}
        </style>
    </head>
    <body>
        <h1>Upload Lua Script</h1>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, msg in messages %}
              <div class="{{category}}">{{ msg }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form method="POST" enctype="multipart/form-data">
            <label>Password: </label><input type="password" name="password" required><br><br>
            <input type="file" name="file" required><br><br>
            <button type="submit">Upload</button>
        </form>

        {% if message %}
            <div class="message">
                <p>{{message}}</p>
                <form method="POST" action="/save">
                    <input type="hidden" name="temp_file" value="{{temp_file}}">
                    <button type="submit">Save</button>
                </form>
            </div>
        {% endif %}
    </body>
    </html>
    """

    return render_template_string(html, message=message, temp_file="temp_uploaded.lua", filename=filename, filesize=filesize)


# Save uploaded file as script.lua
@app.route("/save", methods=["POST"])
def save_file():
    temp_file = request.form.get("temp_file")
    if not temp_file or not os.path.exists(temp_file):
        flash("No uploaded file to save.", "error")
        return redirect(url_for("upload_page"))

    os.replace(temp_file, SCRIPT_FILE)
    flash("Script saved successfully!", "success")
    return redirect(url_for("upload_page"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
