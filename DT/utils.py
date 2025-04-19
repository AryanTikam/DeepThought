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

def get_txt_files_from_folder(folder_path):
    """Returns a list of paths to all .txt files in the specified folder."""
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return []
        
    txt_files = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                txt_files.append(file_path)
    
    return txt_files