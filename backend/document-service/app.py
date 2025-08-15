from flask import Flask, request, jsonify
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)

@app.route('/e2e', methods=['GET'])
def e2e_test():
    return jsonify({'message': 'Document service is reachable'}), 200

@app.route('/documents', methods=['GET'])
def get_documents():
    response = supabase.table('raw_documents').select("*").execute()
    return jsonify(response.data), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)