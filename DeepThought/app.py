from flask import Flask, request, render_template, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
from utils.ner_extraction import extract_entities_from_text
from utils.knowledge_graph import build_knowledge_graph, detect_contradictions, FictionKnowledgeGraph
from utils.explanation_generator import generate_explanation, generate_speculative_boundaries
from utils.document_manager import DocumentManager
import networkx as nx

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

# Initialize document manager and knowledge graph
doc_manager = DocumentManager(storage_dir="uploads")
global_kg = FictionKnowledgeGraph()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "textfile" not in request.files:
        return redirect(request.url)
        
    file = request.files["textfile"]
    if file.filename == "":
        return redirect(request.url)
        
    if file and file.filename.endswith(".txt"):
        # Get metadata
        is_canonical = "canonical" in request.form
        title = request.form.get("title", file.filename)
        author = request.form.get("author", "Unknown")
        year = request.form.get("year", "Unknown")
        
        metadata = {
            "title": title,
            "author": author,
            "year": year
        }
        
        # Add document to manager
        doc_id = doc_manager.add_document(file, metadata, canonical=is_canonical)
        
        # Process the document
        text = doc_manager.get_document_content(doc_id)
        return redirect(url_for("analyze_document", doc_id=doc_id))
    
    return redirect(request.url)

@app.route("/analyze/<doc_id>", methods=["GET"])
def analyze_document(doc_id):
    # Get document content
    text = doc_manager.get_document_content(doc_id)
    if not text:
        return "Document not found", 404
    
    # Extract entities
    extracted_data = extract_entities_from_text(text)
    
    # Build knowledge graph from this document
    document_kg = build_knowledge_graph(extracted_data, source_doc=doc_id)
    
    # Merge with global knowledge graph
    # In a real implementation, you'd need to handle merging more carefully
    for entity_id, info in document_kg.entity_info.items():
        if entity_id not in global_kg.entity_info:
            global_kg.entity_info[entity_id] = info
        else:
            global_kg.entity_info[entity_id]["mentions"].extend(info["mentions"])
    
    # Update the graph
    global_kg.graph = nx.compose(global_kg.graph, document_kg.graph)
    
    # Detect contradictions
    contradictions = detect_contradictions(global_kg)
    
    # Generate explanations for each contradiction
    explanations = []
    for contradiction in contradictions:
        explanation = generate_explanation(contradiction)
        explanations.append(explanation)
    
    # Generate speculation boundaries analysis
    speculation_analysis = generate_speculative_boundaries(global_kg)
    
    document_info = doc_manager.documents[doc_id]
    
    return render_template(
        "results.html",
        document=document_info,
        entities=extracted_data["entities"],
        relationships=extracted_data["relationships"],
        contradictions=contradictions,
        explanations=explanations,
        speculation_analysis=speculation_analysis
    )

@app.route("/documents", methods=["GET"])
def list_documents():
    documents = doc_manager.get_all_documents()
    return render_template("documents.html", documents=documents)

@app.route("/graph", methods=["GET"])
def view_graph():
    # Convert the graph to a format suitable for visualization
    nodes = []
    for entity_id, data in global_kg.graph.nodes(data=True):
        nodes.append({
            "id": entity_id,
            "label": data.get("name", entity_id),
            "group": data.get("type", "Unknown")
        })
    
    links = []
    for source, target, data in global_kg.graph.edges(data=True):
        links.append({
            "source": source,
            "target": target,
            "label": data.get("relation", "related")
        })
    
    return render_template("graph.html", nodes=nodes, links=links)

if __name__ == "__main__":
    app.run(debug=True)