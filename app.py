from flask import Flask, jsonify
from database import Database
import os

app = Flask(__name__)
db = Database()

@app.route('/')
def home():
    return "Hello! Server is running. Database connected: " + str(db.client is not None)

@app.route('/api/products')
def get_products():
    if not db.client:
        return jsonify({"error": "Database not connected"}), 500
    try:
        result = db.client.table('products').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
