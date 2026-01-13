from flask import Flask, request, send_file
import tempfile
import os
from align_video import main  # your existing align_video.py script
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Folder containing reference videos
REFERENCE_FOLDER = os.path.join(os.path.dirname(__file__), "..", "references")

@app.route("/align", methods=["POST"])
def align_video_endpoint():
    if "video" not in request.files:
        return "No video uploaded", 400

    user_file = request.files["video"]

    # Get the reference from form, default to first in folder if not provided
    reference_name = request.form.get("reference", "jhoomar.mp4")
    reference_path = os.path.join(REFERENCE_FOLDER, reference_name)

    if not os.path.exists(reference_path):
        return f"Reference video {reference_name} not found", 400

    # Use a temporary directory for processing
    with tempfile.TemporaryDirectory() as tmpdir:
        user_path = os.path.join(tmpdir, "user.mov")
        output_path = os.path.join(tmpdir, "aligned.mp4")

        # Save uploaded file to temp
        user_file.save(user_path)

        # Run alignment
        main(reference_path, user_path, output_path)

        # Return the aligned video
        return send_file(output_path, mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=True)
