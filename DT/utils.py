# utils.py
import os

UPLOAD_FOLDER = 'uploads'

def load_text_from_file(filepath):
    """Loads text content from a given file path."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading file {filepath}: {e}")
        return None

def ensure_upload_folder():
    """Ensures the upload folder exists."""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)