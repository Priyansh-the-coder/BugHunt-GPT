from flask import Flask, request, jsonify
from functools import wraps
from core.recon.subdomain_enum import enumerate_subdomains
from core.recon.url_collector import collect_urls
from core.recon.param_discovery import discover_all_parameters_sync
from core.recon.subdomain_takeover import check_takeover
from core.utils.burp_proxy import capture_data as burp_capture
from core.recon.port_scanner import scan_ports
from ast import literal_eval
import logging
import os
from core.recon.tech_stack import detect_tech_stack

app = Flask(__name__)


def async_to_sync(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@app.route("/")
def home():
    return "BugHunt-GPT API is live!"

@app.route("/port_scan", methods=["POST"])
def port_scan():
    try:
        data = request.get_json(force=True)
        domain = data.get("domain")

        if not domain:
            return jsonify({"error": "Missing 'domain' in request body"}), 400

        results = scan_ports(domain)
        return jsonify({
            "domain": domain,
            "open_ports": results,
            "count": len(results)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Add this route above the main block
@app.route("/tech_stack", methods=["GET"])
def tech_stack():
    target = request.args.get("domain")
    if not target:
        return jsonify({"error": "Missing 'domain' parameter"}), 400
    
    try:
        results = detect_tech_stack(target)
        
        if "error" in results:
            return jsonify({
                "domain": target,
                "error": results["error"]
            }), 500
        
        return jsonify({
            "domain": target,
            "final_url": results["url"],
            "technologies": results["technologies"],
            "categories": results["categories"],
            "technology_count": len(results["technologies"])
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Unexpected error: {str(e)}"
        }), 500
        
@app.route("/subdomains")
def get_subdomains():
    domain = request.args.get("domain")
    if not domain:
        return "No domain provided", 400

    try:
        results = enumerate_subdomains(domain)
        return str(results), 200
    except Exception as e:
        return str(e), 500

@app.route("/takeover", methods=['POST'])
def run_takeover():
    try:
        raw_data = request.data.decode('utf-8')
        if not raw_data or raw_data=='[]':
            return jsonify({
                "subdomains": [],
                "results": [],
                "message": "No subdomains provided"
            }), 200
        subdomains = literal_eval(raw_data)

        if not isinstance(subdomains, list) or not all(isinstance(i, str) for i in subdomains):
            return "Input must be a Python-style list of strings", 400
        if not subdomains:
            return jsonify({
                "subdomains": [],
                "results": [],
                "message": "Empty subdomain list received"
            }), 200
        takeover_results = check_takeover(subdomains)
        return str(takeover_results), 200

    except Exception as e:
        return str(e), 500

@app.route("/collect_urls")
def collect_urls_endpoint():
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"error": "No domain provided"}), 400

    try:
        # Use the safe version that handles async/sync contexts
        urls = collect_urls(domain)
        return jsonify({"collected_urls": urls})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/param_discovery")
def param_discovery():
    domain = request.args.get("domain")
    try:
        urls = discover_all_parameters_sync(domain)
        return jsonify({"status": "ok", "found_urls": urls})
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


# @app.route('/sub_json_to_list', methods=['POST'])
# def json_to_list():
#     try:
#         data = request.get_json()
#         subdomains = data.get("subdomains", [])
#         if not isinstance(subdomains, list):
#             return jsonify({"error": "subdomains must be a list"}), 400
#         return jsonify({"result": subdomains})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
