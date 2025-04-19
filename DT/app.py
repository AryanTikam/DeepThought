# app.py
import os
import uvicorn
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import io 
from utils import load_text_from_file, ensure_upload_folder, UPLOAD_FOLDER
from processing import analyze_text

load_dotenv()  # Load environment variables from .env

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
    API endpoint to upload one or more .txt files (e.g., via curl -F 'file=@f1.txt' -F 'file=@f2.txt')
    and get consistency analysis based on their combined content.
    Alternatively, use curl -F 'folder=path/to/folder' to analyze all .txt files in a folder.
    """
    # Check if a folder path was provided
    folder_path = request.form.get('folder', None)
    files = []
    
    if folder_path:
        # Process all .txt files in the specified folder
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return jsonify({"error": f"The specified folder '{folder_path}' does not exist or is not a directory"}), 400
            
        for filename in os.listdir(folder_path):
            if allowed_file(filename):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        # Create a file-like object for each file in the folder
                        file_obj = io.BytesIO(f.read())
                        file_obj.filename = filename
                        files.append(file_obj)
    else:
        # Use getlist to handle multiple files with the same field name 'file'
        files = request.files.getlist('file')

    if not files or all(getattr(f, 'filename', '') == '' for f in files):
        return jsonify({"error": "No file part, no selected files, or no valid .txt files in the specified folder"}), 400

    combined_text_content = io.StringIO()  # Use StringIO to build the combined text efficiently
    processed_filenames = []
    total_size = 0

    for file in files:
        if file and getattr(file, 'filename', '') and allowed_file(file.filename):
            filename = secure_filename(file.filename)  # Basic security measure
            try:
                # Read content directly from the file stream
                if hasattr(file, 'read'):
                    content_bytes = file.read()
                else:
                    # If it's already a bytes object from folder processing
                    content_bytes = file.getvalue()
                    
                # Check size limit progressively
                total_size += len(content_bytes)
                if total_size > app.config['MAX_CONTENT_LENGTH']:
                    return jsonify({"error": f"Combined file size exceeds limit of {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)} MB."}), 413  # Payload Too Large

                file_content = content_bytes.decode('utf-8')

                if file_content.strip():  # Only process if file has actual content
                    # Add a separator between files for clarity in processing, if desired
                    if combined_text_content.tell() > 0:  # If not the first file
                        combined_text_content.write("\n\n--- File Separator ---\n\n")
                    combined_text_content.write(file_content)
                    processed_filenames.append(filename)
                else:
                    print(f"Skipping empty file: {filename}")

            except UnicodeDecodeError:
                print(f"Skipping file {filename} due to UTF-8 decoding error.")
            except Exception as e:
                print(f"Error reading file {filename}: {e}")
                return jsonify({"error": f"Could not read file {filename}."}), 500
        elif file and getattr(file, 'filename', '') != '':
            print(f"Skipping non-txt file: {file.filename}")

    final_text_content = combined_text_content.getvalue()
    combined_text_content.close()

    if not processed_filenames:
        return jsonify({"error": "No valid .txt files were provided or found in the request."}), 400
    if not final_text_content.strip():
        return jsonify({"error": "The provided .txt files were empty or contained only whitespace."}), 400

    print(f"Starting analysis for combined content from: {', '.join(processed_filenames)}...")

    try:
        # Perform the analysis using the processing module on the combined text
        analysis_results = analyze_text(final_text_content)
        print(f"Analysis finished for combined content.")

        # Check if analysis itself returned an error
        if isinstance(analysis_results, dict) and "error" in analysis_results:
            print(f"Analysis function returned an error: {analysis_results['error']}")
            return jsonify(analysis_results), 500

        # Return the successful analysis results
        return jsonify(analysis_results), 200

    except Exception as e:
        print(f"An unexpected error occurred during analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"An unexpected server error occurred during analysis: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def home():
    """ Basic welcome route """
    return "Fictional Universe Consistency Kit API is running. POST one or more .txt files to /analyze or specify a folder with .txt files using 'folder' parameter.", 200


if __name__ == "__main__":
    print("Starting Fictional Universe Consistency Kit API...")
    app.run(host="127.0.0.1", port=8000, debug=True)