from fin import file_deleted, folder_deleted, file_uploaded, chat_bot, analysis

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/file_deleted", methods=["POST"])
def file_deleted_api():
    data = request.get_json()
    file_id = data.get("file_id")
    user_id = data.get("user_id")
    result = file_deleted(file_id, user_id)
    return jsonify(result)


@app.route("/folder_deleted", methods=["POST"])
def folder_deleted_api():
    data = request.get_json()
    folder_id = data.get("folder_path")
    result = folder_deleted(folder_id)
    return jsonify(result)


@app.route("/file_uploaded", methods=["POST"])
def file_uploaded_api():
    data = request.get_json()
    file_id = data.get("folder_path")
    user_id = data.get("file_name")
    result = file_uploaded(file_id, user_id)
    return jsonify(result)


@app.route("/chat_bot", methods=["POST"])
def chat_bot_api():
    data = request.get_json()
    user_id = data.get("folder_path")
    message = data.get("message")
    result = chat_bot(user_id, message)
    return jsonify(result)


@app.route("/analysis", methods=["POST"])
def analysis_api():
    data = request.get_json()
    file_id = data.get("folder_path")
    result = analysis(file_id)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
