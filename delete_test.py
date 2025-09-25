#!/usr/bin/env python3
"""
Test the DELETE endpoint for calculations
"""

import requests
import json

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

BACKEND_URL = get_backend_url()
API_BASE_URL = f"{BACKEND_URL}/api"

# Test data
TEST_CALCULATION_DATA = {
    "montantFinancer": "25000",
    "coefficientEmprunteur": "3.5",
    "coefficientCoEmprunteur": "2.0",
    "coefficientComplementaire": "1.0",
    "extensionGarantie": "100",
    "revision": "50",
    "mensualiteEmprunteur": 1500.0,
    "mensualiteCoEmprunteur": 800.0,
    "complementaire": 400.0,
    "mensualitesTotales": 2700.0
}

def test_delete_endpoint():
    print("Testing DELETE endpoint...")
    
    # First create a calculation
    print("1. Creating a calculation to delete...")
    response = requests.post(
        f"{API_BASE_URL}/calculations/",
        json=TEST_CALCULATION_DATA,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create calculation: {response.status_code}")
        return False
        
    created_calc = response.json()
    calc_id = created_calc["id"]
    print(f"✅ Created calculation with ID: {calc_id}")
    
    # Now delete it
    print("2. Deleting the calculation...")
    delete_response = requests.delete(f"{API_BASE_URL}/calculations/{calc_id}", timeout=10)
    
    if delete_response.status_code == 200:
        print("✅ DELETE endpoint works correctly")
        return True
    else:
        print(f"❌ DELETE failed: {delete_response.status_code} - {delete_response.text}")
        return False

if __name__ == "__main__":
    success = test_delete_endpoint()
    print(f"\nDelete test {'PASSED' if success else 'FAILED'}")