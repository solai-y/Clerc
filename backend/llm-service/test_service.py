"""
Simple test script for the LLM classification service
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_prediction():
    """Test prediction endpoint"""
    print("\n🔍 Testing prediction endpoint...")
    
    # Sample document
    test_document = """
    Apple Inc. Reports Fourth Quarter Results
    
    CUPERTINO, California — October 28, 2023 — Apple today announced financial results for its fiscal 2023 fourth quarter ended September 30, 2023. The Company posted quarterly revenue of $89.5 billion, down 1 percent year over year, and quarterly earnings per diluted share of $1.46, up 13 percent year over year.
    
    "Today Apple reports revenue of $89.5 billion for Q4, marking our fourth consecutive quarter of year-over-year revenue decline," said Tim Cook, Apple's CEO. "We are pleased with our performance in challenging circumstances and look forward to the holiday season."
    
    iPhone revenue was $43.8 billion for the quarter, down 3 percent year over year. Mac revenue was $7.6 billion, down 34 percent year over year. iPad revenue was $6.4 billion, down 10 percent year over year. Services revenue reached a new all-time high of $22.3 billion, up 16 percent year over year.
    """
    
    # Test full classification
    request_data = {
        "text": test_document,
        "predict": ["primary", "secondary", "tertiary"],
        "context": {}
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=180
        )
        elapsed = time.time() - start_time
        
        print(f"✅ Prediction completed: {response.status_code} (took {elapsed:.1f}s)")
        
        if response.status_code == 200:
            result = response.json()
            print("\n📊 Classification Results:")
            print(f"Service processing time: {result['elapsed_seconds']:.2f}s")
            
            for level in ['primary', 'secondary', 'tertiary']:
                if level in result['prediction'] and result['prediction'][level]:
                    pred = result['prediction'][level]
                    print(f"\n{level.upper()}:")
                    print(f"  Prediction: {pred['pred']}")
                    print(f"  Confidence: {pred['confidence']:.2f}")
                    if 'key_evidence' in pred and 'supporting' in pred['key_evidence']:
                        evidence = pred['key_evidence']['supporting'][:3]  # Show first 3
                        print(f"  Evidence: {[token['token'] for token in evidence]}")
            
            return True
        else:
            print(f"❌ Prediction failed: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False

def test_context_aware():
    """Test context-aware classification"""
    print("\n🔍 Testing context-aware classification...")
    
    test_document = """
    Goldman Sachs initiates coverage of Tesla with a BUY rating and $300 price target. 
    Our analysis suggests strong growth potential in the EV market and Tesla's competitive advantages in battery technology.
    """
    
    # Test secondary/tertiary prediction with primary context
    request_data = {
        "text": test_document,
        "predict": ["secondary", "tertiary"],
        "context": {"primary": "Recommendations"}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            timeout=180
        )
        
        print(f"✅ Context-aware prediction: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("📊 Results with context:")
            print(f"  Given primary: Recommendations")
            if 'secondary' in result['prediction'] and result['prediction']['secondary']:
                sec = result['prediction']['secondary']
                print(f"  Predicted secondary: {sec['pred']} ({sec['confidence']:.2f})")
            if 'tertiary' in result['prediction'] and result['prediction']['tertiary']:
                ter = result['prediction']['tertiary']
                print(f"  Predicted tertiary: {ter['pred']} ({ter['confidence']:.2f})")
            return True
        else:
            print(f"❌ Context-aware prediction failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Context-aware prediction failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing LLM Classification Service")
    print("=" * 50)
    
    success = True
    success &= test_health()
    success &= test_prediction()
    success &= test_context_aware()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
        print("\nMake sure the service is running:")
        print("  python main.py")