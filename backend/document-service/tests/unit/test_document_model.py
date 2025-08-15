import pytest
import sys
import os

# Add the parent directories to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.document import DocumentModel

class TestDocumentModel:
    """Unit tests for DocumentModel class"""
    
    def test_document_model_valid_data(self):
        """Test DocumentModel with valid data"""
        print("\n[TEST] Testing DocumentModel with valid data...")
        
        data = {
            "document_id": 1,
            "document_name": "Test Document",
            "document_type": "PDF",
            "link": "https://test.com/doc.pdf",
            "categories": [1, 2, 3],
            "uploaded_by": 1,
            "company": 2,
            "upload_date": "2025-01-01T00:00:00+00:00"
        }
        
        doc = DocumentModel(data)
        
        assert doc.document_id == 1
        assert doc.document_name == "Test Document"
        assert doc.document_type == "PDF"
        assert doc.link == "https://test.com/doc.pdf"
        assert doc.categories == [1, 2, 3]
        assert doc.uploaded_by == 1
        assert doc.company == 2
        
        print("[PASS] DocumentModel created successfully with valid data")
    
    def test_document_model_string_sanitization(self):
        """Test string sanitization in DocumentModel"""
        print("\n[TEST] Testing string sanitization...")
        
        data = {
            "document_name": "  Test Document with <script>alert('xss')</script>  ",
            "document_type": "PDF\"malicious",
            "link": "https://test.com/doc.pdf'injection",
            "uploaded_by": 1,
            "company": 1
        }
        
        doc = DocumentModel(data)
        
        # Check that strings are sanitized
        assert doc.document_name == "Test Document with scriptalert(xss)/script"
        assert '"' not in doc.document_type
        assert "'" not in doc.link
        
        print("[PASS] String sanitization works correctly")
    
    def test_document_model_validation_success(self):
        """Test successful validation"""
        print("\n[TEST] Testing successful validation...")
        
        data = {
            "document_name": "Valid Document",
            "document_type": "PDF",
            "link": "https://valid.com/doc.pdf",
            "uploaded_by": 1,
            "company": 1
        }
        
        doc = DocumentModel(data)
        is_valid, errors = doc.validate()
        
        assert is_valid is True
        assert len(errors) == 0
        
        print("[PASS] Validation passed for valid document")
    
    def test_document_model_validation_failures(self):
        """Test validation failures"""
        print("\n[TEST] Testing validation failures...")
        
        # Test missing required fields
        data = {
            "document_name": "",  # Empty name
            "document_type": "",  # Empty type
            "link": "",  # Empty link
            # Missing uploaded_by and company
        }
        
        doc = DocumentModel(data)
        is_valid, errors = doc.validate()
        
        assert is_valid is False
        assert len(errors) > 0
        
        # Check specific error messages
        error_messages = " ".join(errors)
        assert "Document name is required" in error_messages
        assert "Document type is required" in error_messages
        assert "Link is required" in error_messages
        assert "Uploaded by user ID is required" in error_messages
        assert "Company ID is required" in error_messages
        
        print(f"[PASS] Validation correctly failed with {len(errors)} errors")
    
    def test_document_model_categories_validation(self):
        """Test categories field validation"""
        print("\n[TEST] Testing categories validation...")
        
        # Test invalid categories (not a list)
        data = {
            "document_name": "Test",
            "document_type": "PDF",
            "link": "https://test.com/doc.pdf",
            "uploaded_by": 1,
            "company": 1,
            "categories": "not a list"
        }
        
        doc = DocumentModel(data)
        is_valid, errors = doc.validate()
        
        assert is_valid is False
        assert "Categories must be a list" in " ".join(errors)
        
        # Test valid categories (list)
        data["categories"] = [1, 2, 3]
        doc = DocumentModel(data)
        is_valid, errors = doc.validate()
        
        assert is_valid is True
        
        print("[PASS] Categories validation works correctly")
    
    def test_document_model_to_dict(self):
        """Test converting model to dictionary"""
        print("\n[TEST] Testing to_dict method...")
        
        data = {
            "document_id": 1,
            "document_name": "Test Document",
            "document_type": "PDF",
            "link": "https://test.com/doc.pdf",
            "categories": [1, 2],
            "uploaded_by": 1,
            "company": 1,
            "upload_date": "2025-01-01T00:00:00+00:00"
        }
        
        doc = DocumentModel(data)
        
        # Test without ID (for create/update operations)
        result = doc.to_dict(include_id=False)
        
        expected_keys = {"document_name", "document_type", "link", "uploaded_by", "company", "categories", "upload_date"}
        assert set(result.keys()) == expected_keys
        assert "document_id" not in result
        
        # Test with ID (for read operations)
        result_with_id = doc.to_dict(include_id=True)
        assert "document_id" in result_with_id
        assert result_with_id["document_id"] == 1
        
        print("[PASS] to_dict method works correctly")
    
    def test_document_model_integer_validation(self):
        """Test integer field validation"""
        print("\n[TEST] Testing integer validation...")
        
        data = {
            "document_name": "Test",
            "document_type": "PDF",
            "link": "https://test.com/doc.pdf",
            "uploaded_by": "not_an_integer",
            "company": "also_not_an_integer"
        }
        
        doc = DocumentModel(data)
        
        # Integer fields should be None if invalid
        assert doc.uploaded_by is None
        assert doc.company is None
        
        # This should fail validation
        is_valid, errors = doc.validate()
        assert is_valid is False
        
        print("[PASS] Integer validation works correctly")
    
    def test_document_model_date_validation(self):
        """Test date field validation"""
        print("\n[TEST] Testing date validation...")
        
        # Test valid ISO date
        data = {
            "document_name": "Test",
            "document_type": "PDF",
            "link": "https://test.com/doc.pdf",
            "uploaded_by": 1,
            "company": 1,
            "upload_date": "2025-01-01T00:00:00+00:00"
        }
        
        doc = DocumentModel(data)
        assert doc.upload_date == "2025-01-01T00:00:00+00:00"
        
        # Test invalid date
        data["upload_date"] = "invalid_date"
        doc = DocumentModel(data)
        assert doc.upload_date is None
        
        print("[PASS] Date validation works correctly")
    
    def test_document_model_string_length_limit(self):
        """Test string length limits"""
        print("\n[TEST] Testing string length limits...")
        
        long_string = "x" * 300  # Longer than 255 character limit
        
        data = {
            "document_name": long_string,
            "document_type": "PDF",
            "link": "https://test.com/doc.pdf",
            "uploaded_by": 1,
            "company": 1
        }
        
        doc = DocumentModel(data)
        
        # Should be truncated to 255 characters
        assert len(doc.document_name) == 255
        
        print("[PASS] String length limiting works correctly")

if __name__ == "__main__":
    test_model = TestDocumentModel()
    
    tests = [
        test_model.test_document_model_valid_data,
        test_model.test_document_model_string_sanitization,
        test_model.test_document_model_validation_success,
        test_model.test_document_model_validation_failures,
        test_model.test_document_model_categories_validation,
        test_model.test_document_model_to_dict,
        test_model.test_document_model_integer_validation,
        test_model.test_document_model_date_validation,
        test_model.test_document_model_string_length_limit,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"[FAIL] {test.__name__} failed: {e}")
            raise
    
    print("\n[SUCCESS] All DocumentModel unit tests passed!")