import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import custom modules
from models.response import APIResponse
from routes.documents import documents_bp
from services.database import DatabaseService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, origins=['http://localhost:3000'])

# Register blueprints
app.register_blueprint(documents_bp, url_prefix='/documents')

# Initialize database service for health checks
try:
    db_service = DatabaseService()
    logger.info("Document service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize document service: {str(e)}")
    db_service = None

@app.before_request
def log_request():
    """Log incoming requests"""
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")

@app.after_request
def log_response(response):
    """Log outgoing responses"""
    logger.info(f"Response: {response.status_code} - {request.method} {request.path}")
    return response

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return APIResponse.not_found("Endpoint")

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return APIResponse.error("Method not allowed", 405, "METHOD_NOT_ALLOWED")

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return APIResponse.internal_error()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        "service": "document-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Test database connection
    if db_service:
        db_connected, db_error = db_service.test_connection()
        health_status["database_connected"] = db_connected
        if db_error:
            health_status["error"] = db_error
    else:
        health_status["database_connected"] = False
        health_status["error"] = "Database service not initialized"
    
    # Determine overall health
    if health_status["database_connected"]:
        return APIResponse.success(health_status, "Document service is healthy")
    else:
        return APIResponse.error("Document service is unhealthy", 503, "SERVICE_UNHEALTHY")

@app.route('/e2e', methods=['GET'])
def e2e_test():
    """End-to-end test endpoint"""
    logger.info("E2E test endpoint accessed")
    return APIResponse.success({"service": "document-service"}, "Document service is reachable")

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return APIResponse.success({
        "service": "document-service",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Health check",
            "GET /e2e - End-to-end test",
            "GET /documents - Get all documents",
            "GET /documents/<id> - Get document by ID",
            "POST /documents - Create new document",
            "PUT /documents/<id> - Update document",
            "DELETE /documents/<id> - Delete document"
        ]
    }, "Document service API")

if __name__ == '__main__':
    logger.info("Starting document service on port 5003")
    app.run(host='0.0.0.0', port=5003, debug=False)