#!/usr/bin/env python3
"""
API Testing Script for Granteri Voice AI Agent
Tests the FastAPI endpoints to ensure everything is working correctly.
"""

import requests
import json
import os
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_health_endpoint() -> bool:
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_config_endpoint() -> bool:
    """Test the configuration endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Config endpoint passed")
            print(f"   Agent: {data.get('agent_name', 'Unknown')}")
            return True
        else:
            print(f"❌ Config endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Config endpoint failed: {e}")
        return False

def test_make_call_endpoint(phone_number: str = None) -> bool:
    """Test the make call endpoint (dry run)."""
    if not phone_number:
        print("⚠️  Skipping make-call test (no phone number provided)")
        return True
    
    try:
        payload = {
            "phone_number": phone_number,
            "message": "This is a test call from the Granteri API test script."
        }
        
        # Note: This will actually make a call if the server is running
        print(f"🧪 Testing make-call endpoint with {phone_number}")
        print("   (This is a dry run - modify script to actually make calls)")
        
        # Uncomment the following lines to actually test the call endpoint:
        # response = requests.post(f"{BASE_URL}/make-call", 
        #                         json=payload, 
        #                         timeout=10)
        # 
        # if response.status_code == 200:
        #     data = response.json()
        #     print("✅ Make call endpoint passed")
        #     print(f"   Call ID: {data.get('call_id')}")
        #     return True
        # else:
        #     print(f"❌ Make call endpoint failed: {response.status_code}")
        #     return False
        
        print("✅ Make call endpoint test skipped (dry run)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Make call endpoint failed: {e}")
        return False

def test_webhook_endpoint() -> bool:
    """Test the webhook endpoint with a sample payload."""
    try:
        # Sample webhook payload (similar to what Vapi would send)
        sample_payload = {
            "type": "call.started",
            "call": {
                "id": "test_call_123",
                "status": "in-progress",
                "phoneNumber": "+1234567890"
            }
        }
        
        response = requests.post(f"{BASE_URL}/webhook", 
                                json=sample_payload, 
                                timeout=5)
        
        if response.status_code == 200:
            print("✅ Webhook endpoint passed")
            return True
        else:
            print(f"❌ Webhook endpoint failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook endpoint failed: {e}")
        return False

def main():
    """Run all API tests."""
    print("🧪 Granteri Voice AI Agent - API Test Suite")
    print("=" * 50)
    
    # Check if server is running
    print("🔍 Checking if FastAPI server is running...")
    try:
        response = requests.get(BASE_URL, timeout=3)
        print("✅ Server is responding")
    except requests.exceptions.RequestException:
        print("❌ Server is not responding. Please start the server first:")
        print("   python app.py")
        sys.exit(1)
    
    print("\n📊 Running endpoint tests...\n")
    
    results = []
    
    # Test each endpoint
    results.append(("Health Check", test_health_endpoint()))
    results.append(("Configuration", test_config_endpoint()))
    results.append(("Webhook", test_webhook_endpoint()))
    
    # Optional: Test make call with phone number from environment or args
    test_phone = os.getenv("TEST_PHONE_NUMBER")
    if len(sys.argv) > 1:
        test_phone = sys.argv[1]
    
    results.append(("Make Call", test_make_call_endpoint(test_phone)))
    
    # Print summary
    print("\n📋 Test Summary:")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<15} {status}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
