from flask import Flask, request, jsonify
from crunchyroll_api import process_combos  # Import the API functions
import asyncio

# Initialize Flask app
app = Flask(__name__)

@app.route('/check', methods=['POST'])
def check_combos():
    """
    Endpoint to check email:password combos.
    Expects a JSON payload with a "combos" key containing a list of combos.
    """
    data = request.get_json()
    if not data or 'combos' not in data:
        return jsonify({"error": "Please provide a 'combos' key with a list of email:password pairs."}), 400

    combos = data['combos']
    if not isinstance(combos, list):
        return jsonify({"error": "The 'combos' key must contain a list of email:password pairs."}), 400

    # Process the combos asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(process_combos(combos))

    # Format the results
    formatted_results = []
    for email, password, status in results:
        formatted_results.append({
            "email": email,
            "password": password,
            "status": status
        })

    return jsonify({"results": formatted_results})

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
