# app.py
import os
import uvicorn
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from utils import load_text_from_file, ensure_upload_folder, UPLOAD_FOLDER
from processing import analyze_text

load_dotenv() # Load environment variables from .env

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB limit (adjust as needed)

ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/analyze', methods=['POST'])
def analyze_fiction_api():
    """
    API endpoint to upload a .txt file and get consistency analysis.
    """
    ensure_upload_folder() # Make sure the upload folder exists

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename) # Basic security measure
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(filepath)
            print(f"File saved to {filepath}")

            # Load text from the saved file
            text_content = load_text_from_file(filepath)

            if text_content is None:
                 return jsonify({"error": "Could not read the uploaded file content."}), 500

            if not text_content.strip():
                 return jsonify({"error": "Uploaded file is empty."}), 400

            print(f"Starting analysis for {filename}...")
            # Perform the analysis using the processing module
            analysis_results = analyze_text(text_content)
            print(f"Analysis finished for {filename}.")

            # Clean up the uploaded file after processing (optional)
            try:
                os.remove(filepath)
                print(f"Removed temporary file: {filepath}")
            except OSError as e:
                print(f"Error removing temporary file {filepath}: {e}")

            # Check if analysis itself returned an error
            if "error" in analysis_results and "Failed to parse" not in analysis_results.get("error", "") and "unexpected error" not in analysis_results.get("error", ""):
                 # Handle specific errors from processing logic if needed
                 return jsonify(analysis_results), 500 # Internal Server Error for processing issues
            elif "error" in analysis_results:
                 # Handle LLM parsing errors or other major failures
                 return jsonify(analysis_results), 500


            # Return the successful analysis results
            return jsonify(analysis_results), 200

        except Exception as e:
            print(f"An error occurred: {e}")
             # Clean up file even if error occurs mid-processing
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError as e_remove:
                    print(f"Error removing file during error handling {filepath}: {e_remove}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"An unexpected server error occurred: {str(e)}"}), 500
        finally:
             # Optional: Final cleanup check, though should be handled above
             pass

    else:
        return jsonify({"error": "Invalid file type. Only .txt files are allowed."}), 400

@app.route('/', methods=['GET'])
def home():
    """ Basic welcome route """
    return "Fictional Universe Consistency Kit API is running. POST a .txt file to /analyze.", 200


if __name__ == "__main__":
    print("Starting Fictional Universe Consistency Kit API...")
    app.run(host="127.0.0.1", port=8000, debug=True)
