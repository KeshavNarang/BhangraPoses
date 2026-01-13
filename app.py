from flask import Flask, request, send_file, send_from_directory
import tempfile
import os
from backend.align_video import main  # your existing align_video.py
from flask_cors import CORS

# -----------------------------
# Flask setup
# -----------------------------
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
REFERENCE_FOLDER = os.path.join(os.path.dirname(__file__), "references")

app = Flask(__name__, static_folder=frontend_path, static_url_path="")
CORS(app)

# -----------------------------
# Serve frontend
# -----------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    """Serve JS, CSS, or other frontend static files"""
    return send_from_directory(app.static_folder, path)

# -----------------------------
# Serve reference videos
# -----------------------------
@app.route("/references/<path:filename>")
def reference_files(filename):
    return send_from_directory(REFERENCE_FOLDER, filename)

# -----------------------------
# Align video endpoint
# -----------------------------
@app.route("/align", methods=["POST"])
def align_video_endpoint():
    if "video" not in request.files:
        return "No video uploaded", 400

    user_file = request.files["video"]
    reference_name = request.form.get("reference", "jhoomar.mp4")
    reference_path = os.path.join(REFERENCE_FOLDER, reference_name)

    if not os.path.exists(reference_path):
        return f"Reference video {reference_name} not found", 400

    with tempfile.TemporaryDirectory() as tmpdir:
        user_path = os.path.join(tmpdir, "user.mov")
        output_path = os.path.join(tmpdir, "aligned.mp4")

        user_file.save(user_path)
        main(reference_path, user_path, output_path)

        return send_file(output_path, mimetype="video/mp4")

# -----------------------------
# Run Flask
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
