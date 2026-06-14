from flask import Flask, render_template, request, jsonify
from interpreter import parse_and_run_code

app = Flask(__name__, static_url_path='/static',
            static_folder='static', template_folder='templates')


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/interpret", methods=["POST"])
def interpret():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    if not code:
        return jsonify({"error": "No code provided."}), 400
    try:
        result = parse_and_run_code(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "output": "", "steps": [], "ast": None,
            "errors": [{"phase": "Server", "raw": str(e), "friendly": str(e)}],
            "suggestions": [], "symbol_table": {}
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
