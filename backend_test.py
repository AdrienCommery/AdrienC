#!/usr/bin/env python3
"""
SALESBOARD TPL Backend API Testing Suite
Tests all backend functionality including CRUD operations, commission calculations, and statistics.
"""

import requests
import json
from datetime import datetime, date
import uuid
import time

# Configuration
BASE_URL = "https://39ec4bdd-2482-43b6-9c28-51c1ac366160.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def log_pass(self, test_name):
        print(f"✅ PASS: {test_name}")
        self.passed += 1
    
    def log_fail(self, test_name, error):
        print(f"❌ FAIL: {test_name} - {error}")
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")

def test_api_connection():
    """Test basic API connectivity"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("message") == "SALESBOARD TPL API":
                return True, "API connection successful"
            else:
                return False, f"Unexpected response: {data}"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def create_test_sale(vehicle_type="CAMPING-CAR", prix_vente=50000, montant_financement=30000, nombre_pc=2):
    """Create a test sale with realistic data"""
    return {
        "nom": "Dupont",
        "prenom": "Jean",
        "type": vehicle_type,
        "marque": "Pilote",
        "modele": "Galaxy 650",
        "date_vente": "2025-10-15",
        "date_livraison_previsionnelle": "2025-11-15",
        "prix_vente": prix_vente,
        "montant_financement": montant_financement,
        "nombre_pc": nombre_pc,
        "annulation": False
    }

def test_sales_crud_operations(results):
    """Test all CRUD operations for sales"""
    print("\n--- Testing Sales CRUD Operations ---")
    
    # Test POST /api/sales - Create sale
    try:
        test_sale = create_test_sale()
        response = requests.post(f"{BASE_URL}/sales", json=test_sale, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            created_sale = response.json()
            sale_id = created_sale.get("id")
            if sale_id and created_sale.get("nom") == "Dupont":
                results.log_pass("POST /api/sales - Create sale")
            else:
                results.log_fail("POST /api/sales - Create sale", "Invalid response structure")
                return None
        else:
            results.log_fail("POST /api/sales - Create sale", f"HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        results.log_fail("POST /api/sales - Create sale", f"Exception: {str(e)}")
        return None
    
    # Test GET /api/sales - Retrieve all sales
    try:
        response = requests.get(f"{BASE_URL}/sales", timeout=10)
        if response.status_code == 200:
            sales = response.json()
            if isinstance(sales, list) and len(sales) > 0:
                results.log_pass("GET /api/sales - Retrieve all sales")
            else:
                results.log_fail("GET /api/sales - Retrieve all sales", "No sales returned or invalid format")
        else:
            results.log_fail("GET /api/sales - Retrieve all sales", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("GET /api/sales - Retrieve all sales", f"Exception: {str(e)}")
    
    # Test PUT /api/sales/{id} - Update sale (annulation toggle)
    try:
        updated_sale = test_sale.copy()
        updated_sale["annulation"] = True
        response = requests.put(f"{BASE_URL}/sales/{sale_id}", json=updated_sale, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            updated_data = response.json()
            if updated_data.get("annulation") == True:
                results.log_pass("PUT /api/sales/{id} - Update sale (annulation toggle)")
            else:
                results.log_fail("PUT /api/sales/{id} - Update sale", "Annulation not updated correctly")
        else:
            results.log_fail("PUT /api/sales/{id} - Update sale", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("PUT /api/sales/{id} - Update sale", f"Exception: {str(e)}")
    
    # Test DELETE /api/sales/{id} - Delete sale
    try:
        response = requests.delete(f"{BASE_URL}/sales/{sale_id}", timeout=10)
        if response.status_code == 200:
            delete_response = response.json()
            if "deleted successfully" in delete_response.get("message", "").lower():
                results.log_pass("DELETE /api/sales/{id} - Delete sale")
            else:
                results.log_fail("DELETE /api/sales/{id} - Delete sale", "Unexpected delete response")
        else:
            results.log_fail("DELETE /api/sales/{id} - Delete sale", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("DELETE /api/sales/{id} - Delete sale", f"Exception: {str(e)}")
    
    return sale_id

def test_commission_calculation_engine(results):
    """Test commission calculations for different vehicle types"""
    print("\n--- Testing Commission Calculation Engine ---")
    
    # Create test sales for different vehicle types
    test_sales = []
    
    # CAMPING-CAR (should use 5.5% rate)
    camping_car_sale = create_test_sale("CAMPING-CAR", 60000, 40000, 3)
    try:
        response = requests.post(f"{BASE_URL}/sales", json=camping_car_sale, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            test_sales.append(response.json())
            results.log_pass("Create CAMPING-CAR test sale")
        else:
            results.log_fail("Create CAMPING-CAR test sale", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("Create CAMPING-CAR test sale", f"Exception: {str(e)}")
    
    # FOURGON (should use 6.5% rate)
    fourgon_sale = create_test_sale("FOURGON", 45000, 25000, 2)
    try:
        response = requests.post(f"{BASE_URL}/sales", json=fourgon_sale, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            test_sales.append(response.json())
            results.log_pass("Create FOURGON test sale")
        else:
            results.log_fail("Create FOURGON test sale", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("Create FOURGON test sale", f"Exception: {str(e)}")
    
    # VAN (should use 6.5% rate)
    van_sale = create_test_sale("VAN", 55000, 35000, 1)
    try:
        response = requests.post(f"{BASE_URL}/sales", json=van_sale, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            test_sales.append(response.json())
            results.log_pass("Create VAN test sale")
        else:
            results.log_fail("Create VAN test sale", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("Create VAN test sale", f"Exception: {str(e)}")
    
    # Test commission calculations via stats API
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            
            # Check if commission calculations are present
            if "commission_vente" in stats and "commission_financement" in stats:
                commission_vente = stats["commission_vente"]
                commission_financement = stats["commission_financement"]
                
                # Expected calculations:
                # CAMPING-CAR: 60000 * 0.055 = 3300
                # FOURGON: 45000 * 0.065 = 2925  
                # VAN: 55000 * 0.065 = 3575
                # Total expected sales commission: 9800
                
                if commission_vente > 0:
                    results.log_pass("Commission calculation - Sales commission calculated")
                else:
                    results.log_fail("Commission calculation - Sales commission", "No sales commission calculated")
                
                if commission_financement > 0:
                    results.log_pass("Commission calculation - Financing commission calculated")
                else:
                    results.log_fail("Commission calculation - Financing commission", "No financing commission calculated")
                
                results.log_pass("Commission Calculation Engine - Basic functionality")
            else:
                results.log_fail("Commission Calculation Engine", "Commission fields missing from stats")
        else:
            results.log_fail("Commission Calculation Engine", f"Stats API error: HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("Commission Calculation Engine", f"Exception: {str(e)}")
    
    return test_sales

def test_statistics_and_analytics_api(results):
    """Test statistics and analytics API"""
    print("\n--- Testing Statistics and Analytics API ---")
    
    # Test GET /api/stats with default period
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            
            # Check required fields
            required_fields = [
                "vn_livres", "vo_livres", "ventes_annulees", "taux_annulation",
                "ca_cumule", "ca_mensuel", "vehicules_livres_ce_mois",
                "q1_prime_progress", "ca_prime_progress", 
                "commission_vente", "commission_financement"
            ]
            
            missing_fields = [field for field in required_fields if field not in stats]
            if not missing_fields:
                results.log_pass("GET /api/stats - Default period (all required fields present)")
            else:
                results.log_fail("GET /api/stats - Default period", f"Missing fields: {missing_fields}")
            
            # Test Q1 prime progress (should be between 0-35)
            q1_progress = stats.get("q1_prime_progress", -1)
            if 0 <= q1_progress <= 35:
                results.log_pass("Q1 prime progress - Valid range (0-35)")
            else:
                results.log_fail("Q1 prime progress", f"Invalid range: {q1_progress} (expected 0-35)")
            
            # Test CA calculations
            ca_cumule = stats.get("ca_cumule", 0)
            if ca_cumule >= 0:
                results.log_pass("CA cumule calculation - Non-negative value")
            else:
                results.log_fail("CA cumule calculation", f"Negative value: {ca_cumule}")
                
        else:
            results.log_fail("GET /api/stats - Default period", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("GET /api/stats - Default period", f"Exception: {str(e)}")
    
    # Test GET /api/stats with custom period
    try:
        custom_start = "2025-01-01"
        custom_end = "2025-12-31"
        response = requests.get(f"{BASE_URL}/stats?start_date={custom_start}&end_date={custom_end}", timeout=10)
        
        if response.status_code == 200:
            custom_stats = response.json()
            if "ca_cumule" in custom_stats:
                results.log_pass("GET /api/stats - Custom period filtering")
            else:
                results.log_fail("GET /api/stats - Custom period", "Invalid response structure")
        else:
            results.log_fail("GET /api/stats - Custom period", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("GET /api/stats - Custom period", f"Exception: {str(e)}")

def test_commission_configuration_management(results):
    """Test commission configuration management"""
    print("\n--- Testing Commission Configuration Management ---")
    
    # Test GET /api/config - Retrieve default configuration
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            
            # Check required configuration fields
            required_fields = [
                "camping_car_rate", "fourgon_van_rate", "financing_rates",
                "q1_prime_amount", "q1_prime_target", "ca_prime_thresholds"
            ]
            
            missing_fields = [field for field in required_fields if field not in config]
            if not missing_fields:
                results.log_pass("GET /api/config - All required fields present")
            else:
                results.log_fail("GET /api/config", f"Missing fields: {missing_fields}")
            
            # Verify default rates
            if config.get("camping_car_rate") == 0.055:
                results.log_pass("Commission config - CAMPING-CAR rate (5.5%)")
            else:
                results.log_fail("Commission config - CAMPING-CAR rate", f"Expected 0.055, got {config.get('camping_car_rate')}")
            
            if config.get("fourgon_van_rate") == 0.065:
                results.log_pass("Commission config - FOURGON/VAN rate (6.5%)")
            else:
                results.log_fail("Commission config - FOURGON/VAN rate", f"Expected 0.065, got {config.get('fourgon_van_rate')}")
            
            # Verify Q1 prime target
            if config.get("q1_prime_target") == 35:
                results.log_pass("Commission config - Q1 prime target (35 sales)")
            else:
                results.log_fail("Commission config - Q1 prime target", f"Expected 35, got {config.get('q1_prime_target')}")
            
            # Verify CA prime thresholds
            ca_thresholds = config.get("ca_prime_thresholds", {})
            expected_thresholds = {"50000": 5000, "60000": 6000, "70000": 7000, "90000": 11000}
            
            if ca_thresholds == expected_thresholds:
                results.log_pass("Commission config - CA prime thresholds")
            else:
                results.log_fail("Commission config - CA prime thresholds", f"Expected {expected_thresholds}, got {ca_thresholds}")
                
        else:
            results.log_fail("GET /api/config", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("GET /api/config", f"Exception: {str(e)}")
    
    # Test PUT /api/config - Update configuration
    try:
        # Get current config first
        response = requests.get(f"{BASE_URL}/config", timeout=10)
        if response.status_code == 200:
            current_config = response.json()
            
            # Modify a rate for testing
            test_config = current_config.copy()
            test_config["camping_car_rate"] = 0.060  # Change from 5.5% to 6.0%
            
            # Update config
            update_response = requests.put(f"{BASE_URL}/config", json=test_config, headers=HEADERS, timeout=10)
            
            if update_response.status_code == 200:
                updated_config = update_response.json()
                if updated_config.get("camping_car_rate") == 0.060:
                    results.log_pass("PUT /api/config - Update commission rates")
                    
                    # Restore original config
                    requests.put(f"{BASE_URL}/config", json=current_config, headers=HEADERS, timeout=10)
                else:
                    results.log_fail("PUT /api/config", "Rate not updated correctly")
            else:
                results.log_fail("PUT /api/config", f"HTTP {update_response.status_code}: {update_response.text}")
        else:
            results.log_fail("PUT /api/config - Get current config", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("PUT /api/config", f"Exception: {str(e)}")

def cleanup_test_data():
    """Clean up test data created during testing"""
    try:
        # Get all sales
        response = requests.get(f"{BASE_URL}/sales", timeout=10)
        if response.status_code == 200:
            sales = response.json()
            
            # Delete test sales (those with test names)
            for sale in sales:
                if sale.get("nom") in ["Dupont"] and sale.get("prenom") in ["Jean"]:
                    requests.delete(f"{BASE_URL}/sales/{sale['id']}", timeout=10)
            
            print(f"🧹 Cleaned up test data")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {str(e)}")

def main():
    """Main testing function"""
    print("🚀 Starting SALESBOARD TPL Backend API Tests")
    print(f"Testing against: {BASE_URL}")
    
    results = TestResults()
    
    # Test API connection first
    print("\n--- Testing API Connection ---")
    success, message = test_api_connection()
    if success:
        results.log_pass("API Connection")
    else:
        results.log_fail("API Connection", message)
        print("❌ Cannot proceed with tests - API connection failed")
        results.summary()
        return
    
    # Run all test suites
    test_sales_crud_operations(results)
    test_commission_calculation_engine(results)
    test_statistics_and_analytics_api(results)
    test_commission_configuration_management(results)
    
    # Cleanup
    cleanup_test_data()
    
    # Final summary
    results.summary()
    
    # Return success status
    return results.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)