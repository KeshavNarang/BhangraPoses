from flask import Flask, request, send_file, send_from_directory
import tempfile
import os
from align_video import main
from flask_cors import CORS

# Path to your static frontend folder
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app = Flask(__name__, static_folder=frontend_path, static_url_path="")
CORS(app)

# Path to reference videos
REFERENCE_FOLDER = os.path.join(os.path.dirname(__file__), "..", "references")

@app.route("/test")
def test():
    import os
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    index_exists = os.path.exists(os.path.join(frontend_path, "index.html"))
    return f"Frontend folder: {frontend_path}<br>index.html exists? {index_exists}"

# Serve the main page
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# Serve other static files (JS, CSS)
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

# Endpoint to align video
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

# Run Flask on Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway sets this automatically
    app.run(host="0.0.0.0", port=port)
