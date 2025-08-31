from flask import Flask, request, jsonify
import boto3
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
from uuid import uuid4

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
    try:
        # ---- diagnostics (remove or keep) ----
        print("CT:", request.headers.get("content-type"))
        print("Len:", request.headers.get("content-length"))
        print("Files keys:", list(request.files.keys()))
        print("Form keys:", list(request.form.keys()))

        # 0) Basic env validation (helps catch bucket/creds issues early)
        missing_env = [k for k, v in {
            "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
            "AWS_REGION": AWS_REGION,
            "S3_BUCKET_NAME": S3_BUCKET_NAME,
        }.items() if not v]
        if missing_env:
            return jsonify({"error": f"Server misconfigured: missing {', '.join(missing_env)}"}), 500

        # 1) Ensure a file part exists and is not empty
        file = request.files.get('file')
        if file is None:
            return jsonify({"error": "No file provided (expected form field 'file')"}), 400

        # 2) Guard filename; it can be None or ''
        raw_name = file.filename or f"upload_{uuid4().hex}.pdf"
        # If the incoming file has no extension and says it's a PDF, give it .pdf
        if '.' not in raw_name and (file.mimetype == "application/pdf"):
            raw_name = raw_name + ".pdf"
        filename = secure_filename(raw_name) or f"upload_{uuid4().hex}.pdf"

        # 3) Validate "PDF" loosely (browser may send octet-stream, or filename decides)
        mimetype = (file.mimetype or "").lower()
        is_pdf = (
            mimetype == "application/pdf" or
            filename.lower().endswith(".pdf")
        )
        if not is_pdf:
            return jsonify({"error": "File is not a PDF"}), 400

        # 4) Size check without relying on file.content_length (often None)
        #    If you really need a hard 100MB limit, you can trust Nginx client_max_body_size.
        #    If you want to enforce here, read at most 100MB+1 and fail if exceeded.
        file.stream.seek(0, os.SEEK_END)
        size = file.stream.tell()
        file.stream.seek(0)
        if size == 0:
            return jsonify({"error": "Empty file"}), 400
        if size > 100 * 1024 * 1024:
            return jsonify({"error": "File is too large (>100MB)"}), 400

        # 5) Build S3 key and upload
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        key = f"uploads/{timestamp}-{filename}"

        # IMPORTANT: ensure stream is at start before upload (we just seeked)
        file.stream.seek(0)

        s3_client.upload_fileobj(
            file.stream,            # use the stream explicitly
            S3_BUCKET_NAME,
            key,
            ExtraArgs={
                "ContentType": "application/pdf",
                "ContentDisposition": "inline",
            }
        )

        return jsonify({
            "message": "File uploaded successfully",
            "file_key": key,
            "s3_url": f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
        }), 200

    except Exception as e:
        # Log full stack in server logs if you can; keep client message simple
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5003, debug=True, host='0.0.0.0')
