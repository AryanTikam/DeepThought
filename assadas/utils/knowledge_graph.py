from collections import defaultdict


def build_knowledge_graph(entities):
    graph = defaultdict(list)
    for ent in entities:
        graph[ent["type"]].append(ent["name"])
    return dict(graph)


def detect_contradictions(graph):
    contradictions = []
    characters = graph.get("PERSON", [])
    locations = graph.get("GPE", []) + graph.get("LOC", [])

    if "Gavin" in characters and len(locations) > 1:
        contradictions.append(
            {
                "type": "Timeline",
                "description": f"Gavin appears in multiple locations: {', '.join(locations)}.",
            }
        )
    return contradictions
