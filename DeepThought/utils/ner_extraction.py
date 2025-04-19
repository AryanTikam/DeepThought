# utils/ner_extraction.py
import spacy
from spacy.pipeline import EntityRuler
import re

nlp = spacy.load("en_core_web_sm")

# Add custom entity patterns for fiction-specific elements
# New SpaCy API requires adding the ruler with a name
if "entity_ruler" not in nlp.pipe_names:
    ruler = nlp.add_pipe("entity_ruler", before="ner")
else:
    ruler = nlp.get_pipe("entity_ruler")

patterns = [
    {"label": "ABILITY", "pattern": [{"LOWER": {"IN": ["telekinesis", "telepathy", "invisibility", "flight"]}}]},
    {"label": "SPECIES", "pattern": [{"LOWER": {"IN": ["elf", "dwarf", "alien", "vampire", "werewolf"]}}]},
    {"label": "ARTIFACT", "pattern": [{"LOWER": {"IN": ["sword", "ring", "wand", "amulet"]}}, {"LOWER": "of"}, {"POS": "PROPN"}]}
]
ruler.add_patterns(patterns)

def extract_entities_from_text(text):
    doc = nlp(text)
    entities = []
    
    # Extract standard named entities
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "EVENT", "WORK_OF_ART", "DATE", "TIME", "ABILITY", "SPECIES", "ARTIFACT"]:
            entities.append({
                "type": ent.label_, 
                "name": ent.text,
                "context": text[max(0, ent.start_char-50):min(len(text), ent.end_char+50)]
            })
    
    # Extract relationships using simple patterns (to be expanded)
    relationships = extract_relationships(text)
    
    return {"entities": entities, "relationships": relationships}

def extract_relationships(text):
    relationships = []
    
    # Simple patterns for character relationships
    family_patterns = [
        (r"(\w+) is the (father|mother|brother|sister|son|daughter) of (\w+)", "FAMILY"),
        (r"(\w+) and (\w+) are (married|siblings|cousins|enemies|allies)", "RELATION")
    ]
    
    for pattern, rel_type in family_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if rel_type == "FAMILY":
                entity1, relation, entity2 = match.groups()
                relationships.append({
                    "source": entity1,
                    "relation": relation,
                    "target": entity2
                })
            else:
                entity1, entity2, relation = match.groups()
                relationships.append({
                    "source": entity1,
                    "relation": relation,
                    "target": entity2
                })
    
    return relationships