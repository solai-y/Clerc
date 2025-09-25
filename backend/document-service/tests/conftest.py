"""
Test configuration and fixtures for document-service tests
"""
import pytest
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Setup test data that all tests can use"""
    
    # Initialize Supabase client
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        pytest.skip("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Create a test user in access_control table if it doesn't exist
        test_user_data = {
            "user": "test_user",
            "api_key": "test_api_key_123"
        }
        
        # Check if test user already exists
        existing_user = supabase.table('access_control').select("access_id").eq('user', 'test_user').execute()
        
        if not existing_user.data:
            # Create test user
            result = supabase.table('access_control').insert(test_user_data).execute()
            if result.data:
                print(f"Created test user with access_id: {result.data[0]['access_id']}")
        
        # Create a test company if it doesn't exist
        test_company_data = {
            "company_name": "Test Company"
        }
        
        existing_company = supabase.table('companies').select("company_id").eq('company_name', 'Test Company').execute()
        
        if not existing_company.data:
            result = supabase.table('companies').insert(test_company_data).execute()
            if result.data:
                print(f"Created test company with company_id: {result.data[0]['company_id']}")
        
        yield
        
        # Cleanup - Remove test data after all tests
        # Note: This will cascade delete all related documents
        supabase.table('access_control').delete().eq('user', 'test_user').execute()
        supabase.table('companies').delete().eq('company_name', 'Test Company').execute()
        
    except Exception as e:
        print(f"Error setting up test data: {e}")
        pytest.skip(f"Cannot setup test environment: {e}")


@pytest.fixture
def test_user_id():
    """Get the test user ID"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    result = supabase.table('access_control').select("access_id").eq('user', 'test_user').execute()
    if result.data:
        return result.data[0]['access_id']
    return 1  # Fallback


@pytest.fixture
def test_company_id():
    """Get the test company ID"""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    result = supabase.table('companies').select("company_id").eq('company_name', 'Test Company').execute()
    if result.data:
        return result.data[0]['company_id']
    return 1  # Fallback