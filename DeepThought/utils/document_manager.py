# utils/document_manager.py
import os
import uuid
from datetime import datetime

class DocumentManager:
    def __init__(self, storage_dir="uploads"):
        self.storage_dir = storage_dir
        self.documents = {}
        self.hierarchy = []  # List of document IDs in order of precedence
        os.makedirs(storage_dir, exist_ok=True)
    
    def add_document(self, file, metadata=None, canonical=False):
        """Add a document to the manager"""
        if not metadata:
            metadata = {}
            
        doc_id = str(uuid.uuid4())
        filename = os.path.basename(file.filename)
        filepath = os.path.join(self.storage_dir, f"{doc_id}_{filename}")
        
        # Save the file
        file.save(filepath)
        
        # Add to documents dictionary
        self.documents[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "filepath": filepath,
            "added_date": datetime.now(),
            "canonical": canonical,
            "metadata": metadata
        }
        
        # Add to hierarchy (canonical documents go first)
        if canonical:
            self.hierarchy.insert(0, doc_id)
        else:
            self.hierarchy.append(doc_id)
            
        return doc_id
    
    def get_document_content(self, doc_id):
        """Get the content of a document"""
        if doc_id not in self.documents:
            return None
            
        with open(self.documents[doc_id]["filepath"], "r", encoding="utf-8") as f:
            return f.read()
    
    def get_all_documents(self):
        """Get all documents in hierarchy order"""
        return [self.documents[doc_id] for doc_id in self.hierarchy]
    
    def set_hierarchy(self, new_hierarchy):
        """Update the document hierarchy"""
        # Verify all IDs exist
        for doc_id in new_hierarchy:
            if doc_id not in self.documents:
                raise ValueError(f"Document ID {doc_id} not found")
                
        self.hierarchy = new_hierarchy