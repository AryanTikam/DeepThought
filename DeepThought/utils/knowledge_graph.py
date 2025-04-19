# utils/knowledge_graph.py
from collections import defaultdict
import networkx as nx
from datetime import datetime

class FictionKnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.entity_info = {}
        self.timeline = defaultdict(list)
        
    def add_entity(self, entity, source_doc=None, confidence=1.0):
        """Add an entity to the graph with metadata"""
        entity_id = f"{entity['type']}:{entity['name']}"
        
        if entity_id not in self.entity_info:
            self.entity_info[entity_id] = {
                "type": entity["type"],
                "name": entity["name"],
                "mentions": [],
                "attributes": defaultdict(list),
                "first_appearance": source_doc,
                "confidence": confidence
            }
        
        if source_doc:
            self.entity_info[entity_id]["mentions"].append(source_doc)
            
        # Add to graph if not present
        if not self.graph.has_node(entity_id):
            self.graph.add_node(entity_id, 
                               type=entity["type"], 
                               name=entity["name"],
                               confidence=confidence)
        
        return entity_id
            
    def add_relationship(self, source_entity, relation, target_entity, source_doc=None, confidence=1.0):
        """Add a relationship between entities"""
        source_id = self.add_entity(source_entity, source_doc, confidence)
        target_id = self.add_entity(target_entity, source_doc, confidence)
        
        self.graph.add_edge(source_id, target_id, 
                          relation=relation, 
                          source=source_doc,
                          confidence=confidence)
    
    def add_attribute(self, entity, attribute, value, source_doc=None, confidence=1.0):
        """Add an attribute to an entity"""
        entity_id = self.add_entity(entity, source_doc, confidence)
        self.entity_info[entity_id]["attributes"][attribute].append({
            "value": value,
            "source": source_doc,
            "confidence": confidence
        })
    
    def add_timeline_event(self, entity, event, timestamp, source_doc=None, confidence=1.0):
        """Add a timeline event for an entity"""
        entity_id = self.add_entity(entity, source_doc, confidence)
        self.timeline[entity_id].append({
            "event": event,
            "timestamp": timestamp,
            "source": source_doc,
            "confidence": confidence
        })
        
        # Sort timeline events by timestamp
        self.timeline[entity_id].sort(key=lambda x: x["timestamp"])

def build_knowledge_graph(entities_data, source_doc=None):
    """Build a knowledge graph from extracted entities and relationships"""
    kg = FictionKnowledgeGraph()
    
    # Add all entities
    for entity in entities_data["entities"]:
        kg.add_entity(entity, source_doc)
    
    # Add all relationships
    for rel in entities_data["relationships"]:
        source_entity = {"type": "PERSON", "name": rel["source"]}  # Assuming people for simplicity
        target_entity = {"type": "PERSON", "name": rel["target"]}
        kg.add_relationship(source_entity, rel["relation"], target_entity, source_doc)
    
    return kg

def detect_contradictions(knowledge_graph):
    """Detect various types of contradictions in the knowledge graph"""
    contradictions = []
    
    # Check for character location contradictions
    characters = [entity for entity_id, entity in knowledge_graph.entity_info.items() 
                 if entity["type"] == "PERSON"]
    
    locations = [entity for entity_id, entity in knowledge_graph.entity_info.items()
                if entity["type"] in ["GPE", "LOC"]]
    
    # Example contradiction detection: Character in multiple locations
    for character in characters:
        char_locations = []
        for loc in locations:
            # Check if this character is connected to this location
            if knowledge_graph.graph.has_edge(f"PERSON:{character['name']}", f"{loc['type']}:{loc['name']}"):
                char_locations.append(loc["name"])
        
        if len(char_locations) > 1:
            contradictions.append({
                "type": "Location",
                "description": f"{character['name']} appears in multiple locations simultaneously: {', '.join(char_locations)}."
            })
    
    # Check for timeline contradictions
    for entity_id, timeline in knowledge_graph.timeline.items():
        if len(timeline) <= 1:
            continue
            
        # Check for impossible timeline sequences
        for i in range(len(timeline) - 1):
            if timeline[i]["timestamp"] > timeline[i+1]["timestamp"]:
                entity_name = knowledge_graph.entity_info[entity_id]["name"]
                contradictions.append({
                    "type": "Timeline",
                    "description": f"Timeline contradiction for {entity_name}: {timeline[i]['event']} occurs after {timeline[i+1]['event']}."
                })
    
    # Check for attribute contradictions
    for entity_id, info in knowledge_graph.entity_info.items():
        for attribute, values in info["attributes"].items():
            if len(values) <= 1:
                continue
                
            # Check for different values of the same attribute
            unique_values = set(item["value"] for item in values)
            if len(unique_values) > 1:
                contradictions.append({
                    "type": "Attribute",
                    "description": f"{info['name']} has conflicting {attribute} values: {', '.join(unique_values)}."
                })
    
    return contradictions