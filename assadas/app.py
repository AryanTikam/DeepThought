from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import os
import uuid

from utils.ner_extraction import extract_entities_from_text
from utils.knowledge_graph import build_knowledge_graph, detect_contradictions
from utils.explanation_generator import generate_explanation

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["textfile"]
        if file and file.filename.endswith(".txt"):
            filename = secure_filename(file.filename)
            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"], f"{uuid.uuid4()}_{filename}"
            )
            file.save(filepath)

            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            entities = extract_entities_from_text(text)
            graph = build_knowledge_graph(entities)
            contradictions = detect_contradictions(graph)
            explanations = [generate_explanation(c) for c in contradictions]

            return render_template(
                "results.html",
                entities=entities,
                contradictions=contradictions,
                explanations=explanations,
            )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
