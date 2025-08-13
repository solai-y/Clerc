from flask import Flask, request, jsonify
import boto3
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime

# Load .env variables
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Flask app
app = Flask(__name__)

# S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

@app.route('/e2e', methods=['GET'])
def e2e_test():
    return jsonify({'message': 'S3 service is reachable'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    # check if file is pdf
    # if not file.content_type == "application/pdf":
        # return jsonify({"error": "File is not a PDF"}), 400

    try:
        filename = secure_filename(file.filename)
        key = f"uploads/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{filename}"

        s3_client.upload_fileobj(
            file,
            S3_BUCKET_NAME,
            key,
            ExtraArgs={
                "ContentType": file.content_type,
                "ContentDisposition": "inline"     # tells browser to preview the file instead of downloading it
            }
        )

        return jsonify({
            "message": "File uploaded successfully",
            "file_key": key,
            "s3_url": f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5003, debug=True, host='0.0.0.0')
