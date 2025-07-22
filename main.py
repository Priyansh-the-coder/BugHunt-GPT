from flask import Flask, request, jsonify
from core.recon.subdomain_enum import enumerate_subdomains

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def run_enum():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({'error': 'domain param is required'}), 400
    try:
        results = enumerate_subdomains(domain)
        return jsonify({'live_subdomains': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
