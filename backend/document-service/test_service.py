#!/usr/bin/env python3
"""
Simple test runner for Document Service
Runs tests that work in the current environment
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5003"

def test_service_health():
    """Test service health and availability"""
    print("🏥 Testing service health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        
        assert response.status_code in [200, 503]
        assert "status" in data
        assert "data" in data
        
        if response.status_code == 200:
            print("✅ Service is healthy")
        else:
            print("⚠️  Service is unhealthy but responding")
            
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_basic_endpoints():
    """Test basic endpoints"""
    print("🔍 Testing basic endpoints...")
    
    endpoints = [
        ("/e2e", "E2E endpoint"),
        ("/documents", "Documents listing"),
        ("/", "Root endpoint")
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            data = response.json()
            
            assert response.status_code == 200
            assert data.get("status") == "success"
            
            print(f"✅ {description}: OK")
            results.append(True)
            
        except Exception as e:
            print(f"❌ {description}: FAILED - {e}")
            results.append(False)
    
    return all(results)

def test_crud_operations():
    """Test CRUD operations"""
    print("🔄 Testing CRUD operations...")
    
    # CREATE
    try:
        create_data = {
            "document_name": "Test CRUD Document",
            "document_type": "PDF", 
            "link": "https://test.com/crud-test.pdf",
            "uploaded_by": 1,
            "company": 1,
            "categories": [1, 2]
        }
        
        response = requests.post(
            f"{BASE_URL}/documents",
            json=create_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        
        document_id = data["data"]["document_id"]
        print(f"✅ CREATE: Document created with ID {document_id}")
        
        # READ
        response = requests.get(f"{BASE_URL}/documents/{document_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["document_id"] == document_id
        print("✅ READ: Document retrieved successfully")
        
        # UPDATE
        update_data = {
            "document_name": "Updated CRUD Document",
            "document_type": "PDF",
            "link": "https://test.com/crud-test-updated.pdf", 
            "uploaded_by": 1,
            "company": 1,
            "categories": [1, 2, 3]
        }
        
        response = requests.put(
            f"{BASE_URL}/documents/{document_id}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["document_name"] == "Updated CRUD Document"
        print("✅ UPDATE: Document updated successfully")
        
        # DELETE
        response = requests.delete(f"{BASE_URL}/documents/{document_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/documents/{document_id}")
        assert response.status_code == 404
        print("✅ DELETE: Document deleted successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        return False

def test_search_and_pagination():
    """Test search and pagination features"""
    print("🔍 Testing search and pagination...")
    
    try:
        # Test search
        response = requests.get(f"{BASE_URL}/documents?search=Financial&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify search results
        for doc in data["data"]:
            assert "financial" in doc["document_name"].lower()
        
        print("✅ SEARCH: Search functionality works")
        
        # Test pagination
        response = requests.get(f"{BASE_URL}/documents?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) <= 5
        
        print("✅ PAGINATION: Pagination works")
        
        return True
        
    except Exception as e:
        print(f"❌ Search/pagination failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("⚠️  Testing error handling...")
    
    try:
        # Test 404
        response = requests.get(f"{BASE_URL}/documents/99999")
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        print("✅ 404 handling works")
        
        # Test validation error
        invalid_data = {"document_name": "Test"}  # Missing required fields
        response = requests.post(
            f"{BASE_URL}/documents",
            json=invalid_data,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        print("✅ Validation error handling works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("DOCUMENT SERVICE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Service Health", test_service_health),
        ("Basic Endpoints", test_basic_endpoints), 
        ("CRUD Operations", test_crud_operations),
        ("Search & Pagination", test_search_and_pagination),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"💥 {test_name} failed")
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
    
    print(f"\n{'='*60}")
    print(f"TEST RESULTS: {passed}/{total} passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("💥 SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())