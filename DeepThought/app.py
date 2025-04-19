from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import requests
import shutil
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches

# Configure Flask app with static and template folders
app = Flask(
    __name__,
    static_folder="static",  # Path to static files (CSS, JS, etc.)
    template_folder="templates"  # Path to HTML templates
)

# Ensure the universes directory exists
UNIVERSES_DIR = os.path.join(os.getcwd(), "universes")
os.makedirs(UNIVERSES_DIR, exist_ok=True)

# Store analysis results for each universe
universe_analysis = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/add-universe', methods=['POST'])
def add_universe():
    universe_name = request.form.get('name')
    if not universe_name:
        return jsonify({"error": "Universe name is required"}), 400
    
    # Create directory for the universe
    universe_path = os.path.join(UNIVERSES_DIR, universe_name)
    try:
        os.makedirs(universe_path, exist_ok=True)
        return jsonify({"success": True, "path": universe_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload-file', methods=['POST'])
def upload_file():
    universe_id = request.form.get('universeId')
    
    if not universe_id:
        return jsonify({"error": "Universe ID is required"}), 400
    
    universe_name = universe_id.replace('universe-', '')
    universe_path = os.path.join(UNIVERSES_DIR, universe_name)
    
    if not os.path.exists(universe_path):
        os.makedirs(universe_path)
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.txt'):
        filepath = os.path.join(universe_path, file.filename)
        file.save(filepath)
        
        # Call the analysis endpoint
        analyze_universe(universe_path)
        
        return jsonify({
            "success": True, 
            "filename": file.filename,
            "path": filepath
        })
    
    return jsonify({"error": "Only .txt files are allowed"}), 400

@app.route('/get-universe-files', methods=['GET'])
def get_universe_files():
    universe_id = request.args.get('universeId')
    
    if not universe_id:
        return jsonify({"error": "Universe ID is required"}), 400
    
    universe_name = universe_id.replace('universe-', '')
    universe_path = os.path.join(UNIVERSES_DIR, universe_name)
    
    if not os.path.exists(universe_path):
        return jsonify({"files": []})
    
    files = [f for f in os.listdir(universe_path) if f.endswith('.txt')]
    return jsonify({"files": files})

@app.route('/delete-universe', methods=['POST'])
def delete_universe():
    universe_id = request.form.get('universeId')
    
    if not universe_id:
        return jsonify({"error": "Universe ID is required"}), 400
    
    universe_name = universe_id.replace('universe-', '')
    universe_path = os.path.join(UNIVERSES_DIR, universe_name)
    
    if os.path.exists(universe_path):
        try:
            shutil.rmtree(universe_path)
            # Also remove analysis results if they exist
            if universe_id in universe_analysis:
                del universe_analysis[universe_id]
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Universe not found"}), 404

@app.route('/delete-file', methods=['POST'])
def delete_file():
    universe_id = request.form.get('universeId')
    filename = request.form.get('filename')
    
    if not universe_id or not filename:
        return jsonify({"error": "Universe ID and filename are required"}), 400
    
    universe_name = universe_id.replace('universe-', '')
    file_path = os.path.join(UNIVERSES_DIR, universe_name, filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            # Re-analyze the universe after file deletion
            analyze_universe(os.path.join(UNIVERSES_DIR, universe_name))
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "File not found"}), 404

@app.route('/get-knowledge-graph', methods=['GET'])
def get_knowledge_graph():
    universe_id = request.args.get('universeId')
    
    if not universe_id or universe_id not in universe_analysis:
        return jsonify({"error": "No analysis available for this universe"}), 404
    
    knowledge_graph = universe_analysis[universe_id].get("knowledge_graph", {})
    
    # Generate a visual graph using NetworkX
    graph_image = generate_graph_image(knowledge_graph)
    
    return jsonify({
        "knowledge_graph": knowledge_graph,
        "graph_image": graph_image
    })

@app.route('/get-contradictions', methods=['GET'])
def get_contradictions():
    universe_id = request.args.get('universeId')
    
    if not universe_id or universe_id not in universe_analysis:
        return jsonify({"error": "No analysis available for this universe"}), 404
    
    return jsonify({
        "contradictions": universe_analysis[universe_id].get("contradictions", []),
        "speculation_boundaries": universe_analysis[universe_id].get("speculation_boundaries", [])
    })

def generate_graph_image(knowledge_graph):
    """Generate a NetworkX visualization of the knowledge graph"""
    if not knowledge_graph or 'nodes' not in knowledge_graph or 'edges' not in knowledge_graph:
        return None
    
    # Create a NetworkX graph
    G = nx.Graph()
    
    # Node colors based on type
    node_colors = {
        'Character': '#4a6cf7',  # Primary color
        'Location': '#00d4d7',   # Accent color
        'Object': '#ff6b6b',     # Danger color
        'Other': '#6c757d'       # Secondary color
    }
    
    # Node labels and colors
    node_labels = {}
    node_color_map = []
    
    # Add nodes to graph
    for node in knowledge_graph['nodes']:
        G.add_node(node['id'])
        node_labels[node['id']] = node['id']
        node_type = node.get('type', 'Other')
        node_color_map.append(node_colors.get(node_type, node_colors['Other']))
    
    # Add edges to graph
    for edge in knowledge_graph['edges']:
        if edge['source'] in node_labels and edge['target'] in node_labels:
            G.add_edge(edge['source'], edge['target'], 
                      label=edge.get('relationship', ''))
    
    # Create figure
    plt.figure(figsize=(12, 10))
    plt.tight_layout()
    
    # Position nodes using spring layout
    pos = nx.spring_layout(G, k=0.4, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, 
                          node_size=900, 
                          node_color=node_color_map, 
                          alpha=0.9,
                          edgecolors='white',
                          linewidths=2.0)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7, edge_color='#d0d0d0')
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif', 
                           font_weight='bold', font_color='white')
    
    # Draw edge labels (relationships)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                               font_size=8, font_color='#333333',
                               bbox=dict(facecolor='white', edgecolor='none', 
                                        alpha=0.7, boxstyle='round,pad=0.2'))
    
    # Create legend
    legend_elements = [
        mpatches.Patch(color=node_colors['Character'], label='Character'),
        mpatches.Patch(color=node_colors['Location'], label='Location'),
        mpatches.Patch(color=node_colors['Object'], label='Object'),
        mpatches.Patch(color=node_colors['Other'], label='Other')
    ]
    plt.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    # Set background and remove axes
    plt.axis('off')
    
    # Add title
    plt.title('Knowledge Graph Visualization', fontsize=16, pad=20)
    
    # Save figure to BytesIO
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', 
               dpi=100, facecolor='#fcfcff')
    plt.close()
    
    # Convert to base64 for embedding in HTML
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{image_base64}"

def analyze_universe(universe_path):
    """Call the analysis endpoint and store results"""
    try:
        # Make the POST request to analyze the folder
        response = requests.post(
            'http://localhost:8000/analyze',
            files={'folder': (None, universe_path)}
        )
        
        if response.status_code == 200:
            data = response.json()
            universe_id = f"universe-{os.path.basename(universe_path)}"
            universe_analysis[universe_id] = data
            return data
        else:
            print(f"Analysis request failed with status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error analyzing universe: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(debug=True, port=5000)