import os
from flask import Flask, request, jsonify
from core.recon.subdomain_enum import enumerate_subdomains

app = Flask(__name__)

@app.route("/")
def home():
    return "BugHUnt-GPT API is live!"

@app.route("/subdomains")
def get_subdomains():
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"error": "No domain provided"}), 400

    try:
        results = enumerate_subdomains(domain)
        return jsonify({"live_subdomains": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/takeover")
def run_takeover():
    try:
        data = request.get_json()
        subdomains = data.get("subdomains")

        if not subdomains or not isinstance(subdomains, list):
            return jsonify({"error": "Provide a list of subdomains in JSON format"}), 400

        takeover_results = check_takeover(subdomains)
        return jsonify({"takeover_results": takeover_results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
