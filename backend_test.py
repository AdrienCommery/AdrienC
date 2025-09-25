#!/usr/bin/env python3
"""
TPL FINANCE Backend API Test Suite
Tests all backend endpoints for the finance calculation API
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from frontend .env file
def get_backend_url():
    """Read backend URL from frontend .env file"""
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return None

# Configuration
BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    print("ERROR: Could not read REACT_APP_BACKEND_URL from frontend/.env")
    exit(1)

API_BASE_URL = f"{BACKEND_URL}/api"
print(f"Testing API at: {API_BASE_URL}")

# Test data matching the review request
TEST_CALCULATION_DATA = {
    "montantFinancer": "50000",
    "coefficientEmprunteur": "4.5",
    "coefficientCoEmprunteur": "2.5",
    "coefficientComplementaire": "1.5",
    "extensionGarantie": "150",
    "revision": "75",
    "mensualiteEmprunteur": 2250.0,
    "mensualiteCoEmprunteur": 1250.0,
    "complementaire": 750.0,
    "mensualitesTotales": 4475.0
}

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
        
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")
        return self.failed == 0

def test_health_check(results):
    """Test GET /api/ endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "status" in data:
                results.add_pass("Health Check - API is running")
                return True
            else:
                results.add_fail("Health Check", f"Invalid response format: {data}")
                return False
        else:
            results.add_fail("Health Check", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        results.add_fail("Health Check", f"Connection error: {str(e)}")
        return False

def test_create_calculation(results):
    """Test POST /api/calculations endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/calculations/",
            json=TEST_CALCULATION_DATA,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify all required fields are present
            required_fields = [
                "id", "montantFinancer", "coefficientEmprunteur", "coefficientCoEmprunteur",
                "coefficientComplementaire", "extensionGarantie", "revision",
                "mensualiteEmprunteur", "mensualiteCoEmprunteur", "complementaire",
                "mensualitesTotales", "createdAt"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                results.add_fail("Create Calculation", f"Missing fields: {missing_fields}")
                return None
                
            # Verify data matches input
            for key, value in TEST_CALCULATION_DATA.items():
                if data.get(key) != value:
                    results.add_fail("Create Calculation", f"Field {key}: expected {value}, got {data.get(key)}")
                    return None
                    
            # Verify ID is a valid UUID
            try:
                uuid.UUID(data["id"])
            except ValueError:
                results.add_fail("Create Calculation", f"Invalid UUID format for id: {data['id']}")
                return None
                
            # Verify timestamp format
            try:
                datetime.fromisoformat(data["createdAt"].replace('Z', '+00:00'))
            except ValueError:
                results.add_fail("Create Calculation", f"Invalid timestamp format: {data['createdAt']}")
                return None
                
            results.add_pass("Create Calculation - All fields correct")
            return data["id"]
            
        else:
            results.add_fail("Create Calculation", f"HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        results.add_fail("Create Calculation", f"Connection error: {str(e)}")
        return None

def test_get_calculations(results, created_id=None):
    """Test GET /api/calculations endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/calculations/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                results.add_fail("Get Calculations", f"Expected list, got {type(data)}")
                return False
                
            if len(data) == 0:
                results.add_pass("Get Calculations - Empty list (no data)")
                return True
                
            # Verify sorting (newest first)
            if len(data) > 1:
                timestamps = [item.get("createdAt") for item in data]
                sorted_timestamps = sorted(timestamps, reverse=True)
                if timestamps != sorted_timestamps:
                    results.add_fail("Get Calculations", "Results not sorted by createdAt (newest first)")
                    return False
                    
            # If we created a calculation, verify it appears in the list
            if created_id:
                found = any(item.get("id") == created_id for item in data)
                if not found:
                    results.add_fail("Get Calculations", f"Created calculation {created_id} not found in list")
                    return False
                else:
                    results.add_pass("Get Calculations - Created calculation found in list")
                    
            results.add_pass("Get Calculations - Valid response format")
            return True
            
        else:
            results.add_fail("Get Calculations", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        results.add_fail("Get Calculations", f"Connection error: {str(e)}")
        return False

def test_error_handling(results):
    """Test error handling with invalid requests"""
    
    # Test invalid JSON data
    try:
        invalid_data = {
            "montantFinancer": "50000",
            # Missing required fields
        }
        
        response = requests.post(
            f"{API_BASE_URL}/calculations/",
            json=invalid_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [400, 422]:  # Bad Request or Unprocessable Entity
            results.add_pass("Error Handling - Invalid data rejected")
        else:
            results.add_fail("Error Handling", f"Expected 400/422 for invalid data, got {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        results.add_fail("Error Handling", f"Connection error: {str(e)}")
        
    # Test invalid endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/nonexistent/", timeout=10)
        
        if response.status_code == 404:
            results.add_pass("Error Handling - 404 for invalid endpoint")
        else:
            results.add_fail("Error Handling", f"Expected 404 for invalid endpoint, got {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        results.add_fail("Error Handling", f"Connection error: {str(e)}")

def test_data_persistence(results, created_id):
    """Test that data persists by making multiple GET requests"""
    if not created_id:
        results.add_fail("Data Persistence", "No created calculation ID to test persistence")
        return
        
    try:
        # Make multiple requests to ensure data persists
        for i in range(3):
            response = requests.get(f"{API_BASE_URL}/calculations/", timeout=10)
            
            if response.status_code != 200:
                results.add_fail("Data Persistence", f"Request {i+1} failed: HTTP {response.status_code}")
                return
                
            data = response.json()
            found = any(item.get("id") == created_id for item in data)
            
            if not found:
                results.add_fail("Data Persistence", f"Created calculation not found in request {i+1}")
                return
                
        results.add_pass("Data Persistence - Data persists across multiple requests")
        
    except requests.exceptions.RequestException as e:
        results.add_fail("Data Persistence", f"Connection error: {str(e)}")

def main():
    """Run all tests"""
    print("Starting TPL FINANCE Backend API Tests...")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base URL: {API_BASE_URL}")
    print("-" * 60)
    
    results = TestResults()
    
    # Test 1: Health Check
    print("\n1. Testing Health Check Endpoint...")
    health_ok = test_health_check(results)
    
    if not health_ok:
        print("❌ Health check failed - skipping other tests")
        results.summary()
        return False
    
    # Test 2: Create Calculation
    print("\n2. Testing Create Calculation...")
    created_id = test_create_calculation(results)
    
    # Test 3: Get Calculations
    print("\n3. Testing Get Calculations...")
    test_get_calculations(results, created_id)
    
    # Test 4: Data Persistence
    print("\n4. Testing Data Persistence...")
    test_data_persistence(results, created_id)
    
    # Test 5: Error Handling
    print("\n5. Testing Error Handling...")
    test_error_handling(results)
    
    # Final summary
    success = results.summary()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)