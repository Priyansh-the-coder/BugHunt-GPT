import os
from flask import Flask, request, jsonify
from flask.helpers import ensure_async
from core.recon.subdomain_enum import enumerate_subdomains
from core.recon.url_collector import collect_urls
from core.recon.param_discovery import discover_all_parameters
from core.recon.subdomain_takeover import check_takeover
from core.utils.burp_proxy import capture_data as burp_capture
from ast import literal_eval

app = Flask(__name__)

@app.route("/")
def home():
    return "BugHunt-GPT API is live!"

@app.route('/burp_capture', methods=['GET', 'POST'])
def burp_capture_endpoint():  # Remove async here
    if request.method == 'POST':
        url = request.json.get('url')
    else:
        url = request.args.get('url')

    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    async def async_wrapper():
        try:
            data = await burp_capture(url)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return ensure_async(async_wrapper)()

@app.route("/subdomains")
def get_subdomains():
    domain = request.args.get("domain")
    if not domain:
        return "No domain provided", 400

    try:
        results = enumerate_subdomains(domain)
        return str(results), 200  # Return as string representation of a Python list
    except Exception as e:
        return str(e), 500

@app.route("/takeover", methods=['POST'])
def run_takeover():
    try:
        # Read raw data from request body
        raw_data = request.data.decode('utf-8')
        subdomains = literal_eval(raw_data)  # Safely convert string to Python list

        # Validate it's a list of strings
        if not isinstance(subdomains, list) or not all(isinstance(i, str) for i in subdomains):
            return "Input must be a Python-style list of strings", 400

        takeover_results = check_takeover(subdomains)
        return str(takeover_results), 200  # Return Python-style list as string

    except Exception as e:
        return str(e), 500


@app.route("/collect_urls")
def collect_urls_endpoint():
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"error": "No domain provided"}), 400

    try:
        urls = collect_urls(domain)
        return jsonify({"collected_urls": urls})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/param_discovery')
def param_discovery():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400

    try:
        param_names, param_map = discover_all_parameters(domain)

        return jsonify({
            "domain": domain,
            "total_params_found": len(param_names),
            "parameters": list(param_names),
            "param_to_urls": param_map
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sub_json_to_list', methods=['POST'])
def json_to_list():
    try:
        data = request.get_json()
        subdomains = data.get("subdomains", [])
        if not isinstance(subdomains, list):
            return jsonify({"error": "subdomains must be a list"}), 400
        return jsonify({"result": subdomains})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
