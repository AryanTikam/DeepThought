# app.py - Main Flask Application

from flask import Flask, render_template, request, jsonify
import os
import json
import pandas as pd
import networkx as nx
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

app = Flask(__name__)

# Initialize knowledge graph
knowledge_graph = nx.DiGraph()

# Dataset handlers
class DatasetHandler:
    @staticmethod
    def load_comic_characters():
        """Load comic character datasets"""
        try:
            # These would be paths to your downloaded Kaggle datasets
            df1 = pd.read_csv("data/comic_characters_dataset.csv")
            df2 = pd.read_csv("data/comic_characters_dataset_2.csv")
            return pd.concat([df1, df2], ignore_index=True)
        except Exception as e:
            print(f"Error loading comic character data: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def load_fictional_worlds():
        """Load fictional worlds dataset"""
        try:
            return pd.read_csv("data/fictional_worlds_dataset.csv")
        except Exception as e:
            print(f"Error loading fictional worlds data: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def search_gutenberg(query):
        """Mock search of Project Gutenberg content"""
        # In a real implementation, this would connect to Project Gutenberg API
        # or a database of downloaded works
        return f"Found references to '{query}' in Project Gutenberg catalog."

# Feature implementations
class NarrativeAnalyzer:
    def __init__(self):
        self.source_hierarchy = {}
    
    def set_source_hierarchy(self, hierarchy_dict):
        """Set the canon hierarchy for sources"""
        self.source_hierarchy = hierarchy_dict
    
    def extract_elements(self, text, source_name, source_type):
        """Extract narrative elements from text using Gemini"""
        prompt = f"""
        Extract fictional elements from this {source_type} text from {source_name}.
        Identify:
        - Characters (with traits and relationships)
        - Locations (with descriptions)
        - Timeline events
        - World rules or systems (magic, technology, etc.)
        
        Text: {text[:8000]}  # Limiting text length for API constraints
        
        Return as structured JSON with the following format:
        {{
            "characters": [{{name, traits, relationships}}],
            "locations": [{{name, description}}],
            "timeline_events": [{{event, time_reference}}],
            "world_rules": [{{rule_name, description}}]
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            # Parse JSON from response
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # If response isn't valid JSON, we'll try to extract using simple heuristics
                return self._extract_fallback(response.text)
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_fallback(self, text):
        """Fallback extraction when JSON parsing fails"""
        # Basic extraction using string manipulation
        sections = {"characters": [], "locations": [], "timeline_events": [], "world_rules": []}
        current_section = None
        
        for line in text.split('\n'):
            line = line.strip()
            if "characters" in line.lower():
                current_section = "characters"
            elif "locations" in line.lower():
                current_section = "locations"
            elif "timeline" in line.lower() or "events" in line.lower():
                current_section = "timeline_events"
            elif "rules" in line.lower() or "systems" in line.lower():
                current_section = "world_rules"
            elif current_section and line and not line.startswith("#") and not line.startswith("{") and not line.startswith("}"):
                sections[current_section].append({"text": line})
                
        return sections
    
    def resolve_contradiction(self, element1, element2):
        """Resolve contradictions based on source hierarchy"""
        source1 = element1.get("source", "")
        source2 = element2.get("source", "")
        
        rank1 = self.source_hierarchy.get(source1, 999)
        rank2 = self.source_hierarchy.get(source2, 999)
        
        if rank1 < rank2:
            return element1
        else:
            return element2


class WorldModeler:
    def __init__(self, knowledge_graph):
        self.graph = knowledge_graph
        
    def add_element(self, element_type, element_data, source, confidence=1.0):
        """Add an element to the knowledge graph"""
        element_id = f"{element_type}_{element_data.get('name', 'unnamed')}_{hash(str(element_data))}"
        
        if not self.graph.has_node(element_id):
            # Add the node
            self.graph.add_node(
                element_id, 
                type=element_type, 
                data=element_data,
                sources=[source],
                confidence=confidence,
                versions={}
            )
        else:
            # Update existing node
            node_data = self.graph.nodes[element_id]
            if source not in node_data["sources"]:
                node_data["sources"].append(source)
            # Adjust confidence level
            node_data["confidence"] = max(node_data["confidence"], confidence)
            
        return element_id
        
    def connect_elements(self, source_id, target_id, relationship_type, properties=None):
        """Create a relationship between elements"""
        if properties is None:
            properties = {}
            
        self.graph.add_edge(source_id, target_id, type=relationship_type, **properties)
        
    def create_version(self, element_id, version_name, element_data):
        """Create an alternate version (for multiverse/reboot handling)"""
        if self.graph.has_node(element_id):
            node_data = self.graph.nodes[element_id]
            node_data["versions"][version_name] = element_data
            
    def export_subgraph(self, center_element_id, depth=2):
        """Export a subgraph centered on a specific element"""
        if not self.graph.has_node(center_element_id):
            return {"nodes": [], "edges": []}
            
        # Get neighborhood within specified depth
        nodes = nx.single_source_shortest_path_length(self.graph, center_element_id, cutoff=depth)
        subgraph = self.graph.subgraph(nodes)
        
        # Convert to serializable format
        nodes_data = []
        for node in subgraph.nodes:
            node_data = self.graph.nodes[node].copy()
            node_data["id"] = node
            nodes_data.append(node_data)
            
        edges_data = []
        for u, v, data in subgraph.edges(data=True):
            edge_data = data.copy()
            edge_data["source"] = u
            edge_data["target"] = v
            edges_data.append(edge_data)
            
        return {"nodes": nodes_data, "edges": edges_data}


class ContradictionDetector:
    def __init__(self, world_modeler):
        self.world_modeler = world_modeler
        
    def detect_timeline_contradictions(self, character_id):
        """Detect timeline contradictions for a character"""
        if not self.world_modeler.graph.has_node(character_id):
            return []
            
        # Find all timeline events connected to this character
        character_data = self.world_modeler.graph.nodes[character_id]
        contradictions = []
        
        # In a real implementation, we would traverse the graph looking for temporal inconsistencies
        # Here we'll use Gemini for demonstration
        
        character_name = character_data["data"].get("name", "Unknown character")
        events = []
        
        # Collect events related to this character
        for node_id in self.world_modeler.graph.nodes:
            node_data = self.world_modeler.graph.nodes[node_id]
            if node_data["type"] == "timeline_event":
                if character_name in str(node_data["data"]):
                    events.append(node_data["data"])
        
        if len(events) < 2:
            return []
            
        # Use Gemini to analyze timeline consistency
        prompt = f"""
        Analyze these timeline events for the character {character_name} and detect any contradictions:
        
        {json.dumps(events, indent=2)}
        
        Return a list of contradictions, if any, in this JSON format:
        {{
            "contradictions": [
                {{
                    "events": [event_id1, event_id2],
                    "description": "Description of the contradiction",
                    "resolution_options": ["Option 1", "Option 2"]
                }}
            ]
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get("contradictions", [])
        except Exception as e:
            return [{"error": str(e)}]
            
    def detect_rule_contradictions(self):
        """Detect contradictions in world rules"""
        world_rules = []
        
        # Collect all world rules
        for node_id in self.world_modeler.graph.nodes:
            node_data = self.world_modeler.graph.nodes[node_id]
            if node_data["type"] == "world_rule":
                world_rules.append({
                    "id": node_id,
                    "data": node_data["data"],
                    "source": node_data["sources"][0] if node_data["sources"] else "Unknown"
                })
                
        if len(world_rules) < 2:
            return []
        
        # Use Gemini to analyze rule consistency
        prompt = f"""
        Analyze these fictional world rules and detect any logical contradictions:
        
        {json.dumps(world_rules, indent=2)}
        
        Return a list of contradictions, if any, in this JSON format:
        {{
            "contradictions": [
                {{
                    "rules": [rule_id1, rule_id2],
                    "description": "Description of the contradiction",
                    "resolution_options": ["Option 1", "Option 2"]
                }}
            ]
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get("contradictions", [])
        except Exception as e:
            return [{"error": str(e)}]


class SpeculationBoundaryTool:
    def __init__(self, world_modeler):
        self.world_modeler = world_modeler
        
    def analyze_fact_vs_speculation(self, query):
        """Analyze whether a statement is canonical fact or speculation"""
        # Get relevant subgraph elements
        relevant_nodes = []
        
        for node_id in self.world_modeler.graph.nodes:
            node_data = self.world_modeler.graph.nodes[node_id]
            # Simple keyword matching for demonstration
            if any(keyword in query.lower() for keyword in str(node_data["data"]).lower().split()):
                relevant_nodes.append({
                    "id": node_id,
                    "type": node_data["type"],
                    "data": node_data["data"],
                    "confidence": node_data["confidence"],
                    "sources": node_data["sources"]
                })
        
        if not relevant_nodes:
            return {
                "status": "unknown",
                "confidence": 0,
                "explanation": "No related information found in the knowledge base."
            }
            
        # Use Gemini to analyze if the query is fact, speculative, or contradictory
        prompt = f"""
        Determine if this statement about a fictional universe is a confirmed fact, speculation, or contradicts known elements:
        
        Statement: "{query}"
        
        Related known elements:
        {json.dumps(relevant_nodes, indent=2)}
        
        Respond with one of: "fact", "speculation", "contradiction", or "unknown"
        Include a confidence score (0-1) and explanation. Format:
        {{
            "status": "fact|speculation|contradiction|unknown",
            "confidence": 0.7,
            "explanation": "Detailed reasoning"
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            return result
        except Exception as e:
            return {
                "status": "error",
                "confidence": 0,
                "explanation": f"Error in analysis: {str(e)}"
            }
    
    def identify_open_questions(self, universe_name):
        """Identify significant undefined areas in the fictional universe"""
        # Gather all elements related to this universe
        universe_elements = []
        
        for node_id in self.world_modeler.graph.nodes:
            node_data = self.world_modeler.graph.nodes[node_id]
            if universe_name.lower() in str(node_data).lower():
                universe_elements.append({
                    "id": node_id,
                    "type": node_data["type"],
                    "data": node_data["data"]
                })
        
        # Use Gemini to identify open questions
        prompt = f"""
        Based on these elements from the fictional universe "{universe_name}", 
        identify significant open questions or undefined areas that fans might speculate about.
        
        Universe elements:
        {json.dumps(universe_elements, indent=2)}
        
        Return a list of open questions in this JSON format:
        {{
            "open_questions": [
                {{
                    "question": "Open question description",
                    "related_elements": ["element_id1", "element_id2"],
                    "speculation_potential": "high|medium|low",
                    "narrative_impact": "Description of potential narrative impact"
                }}
            ]
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            return result.get("open_questions", [])
        except Exception as e:
            return [{"error": str(e)}]


# Initialize components
dataset_handler = DatasetHandler()
narrative_analyzer = NarrativeAnalyzer()
world_modeler = WorldModeler(knowledge_graph)
contradiction_detector = ContradictionDetector(world_modeler)
speculation_boundary_tool = SpeculationBoundaryTool(world_modeler)

# Sample source hierarchy
narrative_analyzer.set_source_hierarchy({
    "primary_novel": 1,           # Highest authority
    "author_statements": 2,
    "sequel_novels": 3,
    "official_adaptations": 4,
    "licensed_spinoffs": 5,
    "official_companion_books": 6,
    "fan_theories": 10            # Lowest authority
})

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    query_type = data.get('query_type')
    content = data.get('content', '')
    universe = data.get('universe', '')
    source_name = data.get('source_name', '')
    source_type = data.get('source_type', '')
    
    if query_type == 'extract_elements':
        result = narrative_analyzer.extract_elements(content, source_name, source_type)
        
        # Add extracted elements to knowledge graph
        for element_type in ['characters', 'locations', 'timeline_events', 'world_rules']:
            for item in result.get(element_type, []):
                world_modeler.add_element(
                    element_type.rstrip('s'),  # Convert plural to singular
                    item,
                    source_name,
                    confidence=0.8
                )
        
        return jsonify(result)
        
    elif query_type == 'detect_contradictions':
        character_contradictions = []
        rule_contradictions = []
        
        if content:  # If a specific character is provided
            char_id = None
            # Find character node
            for node_id in world_modeler.graph.nodes:
                node_data = world_modeler.graph.nodes[node_id]
                if node_data["type"] == "character" and content.lower() in str(node_data["data"]).lower():
                    char_id = node_id
                    break
            
            if char_id:
                character_contradictions = contradiction_detector.detect_timeline_contradictions(char_id)
        
        rule_contradictions = contradiction_detector.detect_rule_contradictions()
        
        return jsonify({
            "character_contradictions": character_contradictions,
            "rule_contradictions": rule_contradictions
        })
        
    elif query_type == 'fact_check':
        result = speculation_boundary_tool.analyze_fact_vs_speculation(content)
        return jsonify(result)
        
    elif query_type == 'open_questions':
        result = speculation_boundary_tool.identify_open_questions(universe)
        return jsonify(result)
        
    else:
        # Default to using Gemini as a chatbot for fictional universe questions
        prompt = f"""
        Answer this question about fictional universes or narrative consistency:
        "{content}"
        
        If this relates to a specific fictional universe, provide analysis based on canonical sources.
        Distinguish between confirmed facts and fan speculation.
        """
        
        try:
            response = model.generate_content(prompt)
            return jsonify({"response": response.text})
        except Exception as e:
            return jsonify({"error": str(e)})

@app.route('/api/knowledge_graph', methods=['GET'])
def get_knowledge_graph():
    element_id = request.args.get('element_id')
    depth = int(request.args.get('depth', 2))
    
    if element_id:
        subgraph = world_modeler.export_subgraph(element_id, depth)
        return jsonify(subgraph)
    else:
        # Return basic stats
        return jsonify({
            "node_count": world_modeler.graph.number_of_nodes(),
            "edge_count": world_modeler.graph.number_of_edges(),
            "element_types": {
                "character": sum(1 for n in world_modeler.graph.nodes if world_modeler.graph.nodes[n].get("type") == "character"),
                "location": sum(1 for n in world_modeler.graph.nodes if world_modeler.graph.nodes[n].get("type") == "location"),
                "timeline_event": sum(1 for n in world_modeler.graph.nodes if world_modeler.graph.nodes[n].get("type") == "timeline_event"),
                "world_rule": sum(1 for n in world_modeler.graph.nodes if world_modeler.graph.nodes[n].get("type") == "world_rule")
            }
        })

@app.route('/api/search_datasets', methods=['GET'])
def search_datasets():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"results": []})
    
    # Search in comic characters dataset
    comic_chars = dataset_handler.load_comic_characters()
    if not comic_chars.empty:
        char_results = comic_chars[comic_chars.apply(lambda row: query.lower() in str(row).lower(), axis=1)]
        char_results = char_results.head(5).to_dict('records')
    else:
        char_results = []
    
    # Search in fictional worlds dataset
    fictional_worlds = dataset_handler.load_fictional_worlds()
    if not fictional_worlds.empty:
        world_results = fictional_worlds[fictional_worlds.apply(lambda row: query.lower() in str(row).lower(), axis=1)]
        world_results = world_results.head(5).to_dict('records')
    else:
        world_results = []
    
    # Search in Project Gutenberg
    gutenberg_result = dataset_handler.search_gutenberg(query)
    
    return jsonify({
        "results": {
            "characters": char_results,
            "worlds": world_results,
            "gutenberg": gutenberg_result
        }
    })

if __name__ == '__main__':
    app.run(debug=True)