import spacy

nlp = spacy.load("en_core_web_sm")


def extract_entities_from_text(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "EVENT", "WORK_OF_ART"]:
            entities.append({"type": ent.label_, "name": ent.text})
    return entities
