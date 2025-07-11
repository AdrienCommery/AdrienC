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

def test_commission_settings_api(results):
    """Test the new Commission Settings API endpoints"""
    print("\n--- Testing Commission Settings API (NEW FEATURES) ---")
    
    # Test GET /api/commission-rates - Retrieve detailed commission rates
    try:
        response = requests.get(f"{BASE_URL}/commission-rates", timeout=10)
        if response.status_code == 200:
            rates = response.json()
            
            # Check required fields for configuration page
            required_fields = ["payplan_rates", "financing_rates", "q1_prime", "ca_prime_thresholds"]
            missing_fields = [field for field in required_fields if field not in rates]
            
            if not missing_fields:
                results.log_pass("GET /api/commission-rates - All required fields present")
            else:
                results.log_fail("GET /api/commission-rates", f"Missing fields: {missing_fields}")
            
            # Verify payplan_rates structure
            payplan_rates = rates.get("payplan_rates", {})
            if "camping_car" in payplan_rates and "fourgon_van" in payplan_rates:
                results.log_pass("GET /api/commission-rates - Payplan rates structure")
                
                # Verify default rates
                if payplan_rates["camping_car"] == 0.055:
                    results.log_pass("GET /api/commission-rates - CAMPING-CAR rate (5.5%)")
                else:
                    results.log_fail("GET /api/commission-rates - CAMPING-CAR rate", f"Expected 0.055, got {payplan_rates['camping_car']}")
                
                if payplan_rates["fourgon_van"] == 0.065:
                    results.log_pass("GET /api/commission-rates - FOURGON/VAN rate (6.5%)")
                else:
                    results.log_fail("GET /api/commission-rates - FOURGON/VAN rate", f"Expected 0.065, got {payplan_rates['fourgon_van']}")
            else:
                results.log_fail("GET /api/commission-rates - Payplan rates", "Missing camping_car or fourgon_van rates")
            
            # Verify financing_rates structure (0-4 PC)
            financing_rates = rates.get("financing_rates", {})
            expected_pc_keys = ["0", "1", "2", "3", "4"]
            if all(key in financing_rates for key in expected_pc_keys):
                results.log_pass("GET /api/commission-rates - Financing rates (0-4 PC)")
            else:
                results.log_fail("GET /api/commission-rates - Financing rates", f"Missing PC keys, got: {list(financing_rates.keys())}")
            
            # Verify Q1 prime structure
            q1_prime = rates.get("q1_prime", {})
            if "amount" in q1_prime and "target" in q1_prime:
                results.log_pass("GET /api/commission-rates - Q1 prime structure")
                
                if q1_prime["target"] == 35:
                    results.log_pass("GET /api/commission-rates - Q1 prime target (35)")
                else:
                    results.log_fail("GET /api/commission-rates - Q1 prime target", f"Expected 35, got {q1_prime['target']}")
            else:
                results.log_fail("GET /api/commission-rates - Q1 prime", "Missing amount or target fields")
            
            # Verify CA prime thresholds (50, 60, 70, 90 vehicles)
            ca_thresholds = rates.get("ca_prime_thresholds", {})
            expected_vehicle_thresholds = ["50", "60", "70", "90"]
            if all(key in ca_thresholds for key in expected_vehicle_thresholds):
                results.log_pass("GET /api/commission-rates - CA prime thresholds (50, 60, 70, 90 vehicles)")
                
                # Verify threshold values
                expected_values = {"50": 5000, "60": 6000, "70": 7000, "90": 11000}
                if ca_thresholds == expected_values:
                    results.log_pass("GET /api/commission-rates - CA prime threshold values")
                else:
                    results.log_fail("GET /api/commission-rates - CA prime values", f"Expected {expected_values}, got {ca_thresholds}")
            else:
                results.log_fail("GET /api/commission-rates - CA prime thresholds", f"Missing vehicle thresholds, got: {list(ca_thresholds.keys())}")
                
        else:
            results.log_fail("GET /api/commission-rates", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("GET /api/commission-rates", f"Exception: {str(e)}")
    
    # Test PUT /api/commission-rates - Update commission rates
    try:
        # First get current rates
        response = requests.get(f"{BASE_URL}/commission-rates", timeout=10)
        if response.status_code == 200:
            original_rates = response.json()
            
            # Test updating payplan rates
            test_rates = {
                "payplan_rates": {
                    "camping_car": 0.060,  # Change from 5.5% to 6.0%
                    "fourgon_van": 0.070   # Change from 6.5% to 7.0%
                }
            }
            
            update_response = requests.put(f"{BASE_URL}/commission-rates", json=test_rates, headers=HEADERS, timeout=10)
            
            if update_response.status_code == 200:
                update_result = update_response.json()
                if "message" in update_result and "updated successfully" in update_result["message"]:
                    results.log_pass("PUT /api/commission-rates - Update payplan rates")
                    
                    # Verify the update persisted
                    verify_response = requests.get(f"{BASE_URL}/commission-rates", timeout=10)
                    if verify_response.status_code == 200:
                        updated_rates = verify_response.json()
                        if (updated_rates["payplan_rates"]["camping_car"] == 0.060 and 
                            updated_rates["payplan_rates"]["fourgon_van"] == 0.070):
                            results.log_pass("PUT /api/commission-rates - Payplan rates persistence")
                        else:
                            results.log_fail("PUT /api/commission-rates - Persistence", "Updated rates not persisted correctly")
                    else:
                        results.log_fail("PUT /api/commission-rates - Verification", "Could not verify updated rates")
                else:
                    results.log_fail("PUT /api/commission-rates - Response", f"Unexpected response: {update_result}")
            else:
                results.log_fail("PUT /api/commission-rates - Update payplan", f"HTTP {update_response.status_code}: {update_response.text}")
            
            # Test updating financing rates
            test_financing = {
                "financing_rates": {
                    "0": 0.010,  # Change from 0.5% to 1.0%
                    "1": 0.065,  # Change from 6.0% to 6.5%
                    "2": 0.070,  # Change from 6.5% to 7.0%
                    "3": 0.080,  # Change from 7.5% to 8.0%
                    "4": 0.085   # Change from 8.0% to 8.5%
                }
            }
            
            financing_response = requests.put(f"{BASE_URL}/commission-rates", json=test_financing, headers=HEADERS, timeout=10)
            if financing_response.status_code == 200:
                results.log_pass("PUT /api/commission-rates - Update financing rates")
            else:
                results.log_fail("PUT /api/commission-rates - Financing rates", f"HTTP {financing_response.status_code}")
            
            # Test updating Q1 prime
            test_q1 = {
                "q1_prime": {
                    "amount": 2000.0,  # Change from 1500€ to 2000€
                    "target": 40       # Change from 35 to 40
                }
            }
            
            q1_response = requests.put(f"{BASE_URL}/commission-rates", json=test_q1, headers=HEADERS, timeout=10)
            if q1_response.status_code == 200:
                results.log_pass("PUT /api/commission-rates - Update Q1 prime")
            else:
                results.log_fail("PUT /api/commission-rates - Q1 prime", f"HTTP {q1_response.status_code}")
            
            # Test updating CA prime thresholds
            test_ca_prime = {
                "ca_prime_thresholds": {
                    "50": 5500,   # Change from 5000€ to 5500€
                    "60": 6500,   # Change from 6000€ to 6500€
                    "70": 7500,   # Change from 7000€ to 7500€
                    "90": 12000   # Change from 11000€ to 12000€
                }
            }
            
            ca_response = requests.put(f"{BASE_URL}/commission-rates", json=test_ca_prime, headers=HEADERS, timeout=10)
            if ca_response.status_code == 200:
                results.log_pass("PUT /api/commission-rates - Update CA prime thresholds")
            else:
                results.log_fail("PUT /api/commission-rates - CA prime thresholds", f"HTTP {ca_response.status_code}")
            
            # Restore original rates
            try:
                restore_response = requests.put(f"{BASE_URL}/commission-rates", json=original_rates, headers=HEADERS, timeout=10)
                if restore_response.status_code == 200:
                    results.log_pass("PUT /api/commission-rates - Restore original rates")
                else:
                    results.log_fail("PUT /api/commission-rates - Restore", "Could not restore original rates")
            except Exception as e:
                results.log_fail("PUT /api/commission-rates - Restore", f"Exception: {str(e)}")
                
        else:
            results.log_fail("PUT /api/commission-rates - Get original", f"Could not get original rates: HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("PUT /api/commission-rates", f"Exception: {str(e)}")

def test_pdf_export_api(results):
    """Test the new PDF Export API endpoint"""
    print("\n--- Testing PDF Export API (NEW FEATURES) ---")
    
    # Create some test sales data for PDF generation
    test_sales = []
    try:
        # Create a few test sales for the PDF
        camping_car_sale = create_test_sale("CAMPING-CAR", 65000, 45000, 2)
        fourgon_sale = create_test_sale("FOURGON", 50000, 30000, 1)
        
        for sale_data in [camping_car_sale, fourgon_sale]:
            response = requests.post(f"{BASE_URL}/sales", json=sale_data, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                test_sales.append(response.json())
    except Exception as e:
        print(f"⚠️  Could not create test sales for PDF: {str(e)}")
    
    # Test POST /api/export-pdf with default period (2025-09-01 to 2026-08-31)
    try:
        response = requests.post(f"{BASE_URL}/export-pdf", timeout=30)  # Longer timeout for PDF generation
        
        if response.status_code == 200:
            # Check if response is a PDF file
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                results.log_pass("POST /api/export-pdf - Default period (PDF generated)")
                
                # Check file size (should be > 0)
                content_length = len(response.content)
                if content_length > 1000:  # Reasonable PDF size
                    results.log_pass("POST /api/export-pdf - PDF file size check")
                else:
                    results.log_fail("POST /api/export-pdf - File size", f"PDF too small: {content_length} bytes")
                
                # Check filename in headers
                content_disposition = response.headers.get('content-disposition', '')
                if 'salesboard_report_' in content_disposition:
                    results.log_pass("POST /api/export-pdf - Filename format")
                else:
                    results.log_fail("POST /api/export-pdf - Filename", f"Unexpected filename: {content_disposition}")
            else:
                results.log_fail("POST /api/export-pdf - Content type", f"Expected PDF, got: {content_type}")
        else:
            results.log_fail("POST /api/export-pdf - Default period", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("POST /api/export-pdf - Default period", f"Exception: {str(e)}")
    
    # Test POST /api/export-pdf with custom period parameters
    try:
        custom_params = {
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
        }
        
        response = requests.post(f"{BASE_URL}/export-pdf", params=custom_params, timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                results.log_pass("POST /api/export-pdf - Custom period parameters")
                
                # Check filename includes custom dates
                content_disposition = response.headers.get('content-disposition', '')
                if '2025-01-01' in content_disposition and '2025-12-31' in content_disposition:
                    results.log_pass("POST /api/export-pdf - Custom period filename")
                else:
                    results.log_fail("POST /api/export-pdf - Custom filename", f"Dates not in filename: {content_disposition}")
            else:
                results.log_fail("POST /api/export-pdf - Custom period content", f"Expected PDF, got: {content_type}")
        else:
            results.log_fail("POST /api/export-pdf - Custom period", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("POST /api/export-pdf - Custom period", f"Exception: {str(e)}")
    
    # Test error handling for invalid date formats
    try:
        invalid_params = {
            "start_date": "invalid-date",
            "end_date": "2025-12-31"
        }
        
        response = requests.post(f"{BASE_URL}/export-pdf", params=invalid_params, timeout=10)
        
        if response.status_code == 400:
            results.log_pass("POST /api/export-pdf - Invalid date format error handling")
        elif response.status_code == 500:
            # Check if error message mentions date format
            error_text = response.text.lower()
            if 'date' in error_text or 'format' in error_text:
                results.log_pass("POST /api/export-pdf - Invalid date error handling (500 with date error)")
            else:
                results.log_fail("POST /api/export-pdf - Invalid date error", f"Unexpected 500 error: {response.text}")
        else:
            results.log_fail("POST /api/export-pdf - Invalid date handling", f"Expected 400/500, got HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("POST /api/export-pdf - Invalid date handling", f"Exception: {str(e)}")
    
    # Test PDF generation with existing sales data vs empty data
    try:
        # Test with a period that should have no sales
        empty_params = {
            "start_date": "2020-01-01",
            "end_date": "2020-12-31"
        }
        
        response = requests.post(f"{BASE_URL}/export-pdf", params=empty_params, timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                results.log_pass("POST /api/export-pdf - Empty data period (PDF still generated)")
            else:
                results.log_fail("POST /api/export-pdf - Empty data", f"Expected PDF, got: {content_type}")
        else:
            results.log_fail("POST /api/export-pdf - Empty data period", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("POST /api/export-pdf - Empty data period", f"Exception: {str(e)}")
    
    # Clean up test sales created for PDF testing
    try:
        for sale in test_sales:
            requests.delete(f"{BASE_URL}/sales/{sale['id']}", timeout=10)
    except Exception as e:
        print(f"⚠️  Could not clean up PDF test sales: {str(e)}")

def test_integration_scenarios(results):
    """Test integration scenarios between commission settings and PDF export"""
    print("\n--- Testing Integration Scenarios (NEW FEATURES) ---")
    
    try:
        # 1. Update commission rates and verify stats calculation changes
        original_response = requests.get(f"{BASE_URL}/commission-rates", timeout=10)
        if original_response.status_code != 200:
            results.log_fail("Integration test setup", "Could not get original commission rates")
            return
        
        original_rates = original_response.json()
        
        # Create a test sale
        test_sale = create_test_sale("CAMPING-CAR", 100000, 50000, 2)
        sale_response = requests.post(f"{BASE_URL}/sales", json=test_sale, headers=HEADERS, timeout=10)
        if sale_response.status_code != 200:
            results.log_fail("Integration test setup", "Could not create test sale")
            return
        
        created_sale = sale_response.json()
        
        # Get initial stats
        initial_stats = requests.get(f"{BASE_URL}/stats", timeout=10)
        if initial_stats.status_code != 200:
            results.log_fail("Integration test", "Could not get initial stats")
            return
        
        initial_commission = initial_stats.json()["commission_vente"]
        
        # Update commission rates (increase CAMPING-CAR rate)
        updated_rates = {
            "payplan_rates": {
                "camping_car": 0.080,  # Increase from 5.5% to 8.0%
                "fourgon_van": 0.065
            }
        }
        
        update_response = requests.put(f"{BASE_URL}/commission-rates", json=updated_rates, headers=HEADERS, timeout=10)
        if update_response.status_code == 200:
            # Get updated stats
            updated_stats = requests.get(f"{BASE_URL}/stats", timeout=10)
            if updated_stats.status_code == 200:
                updated_commission = updated_stats.json()["commission_vente"]
                
                # Commission should have increased (100000 * 0.08 vs 100000 * 0.055)
                if updated_commission > initial_commission:
                    results.log_pass("Integration - Commission rate update affects stats calculation")
                else:
                    results.log_fail("Integration - Stats calculation", f"Commission not updated: {initial_commission} -> {updated_commission}")
            else:
                results.log_fail("Integration - Updated stats", f"HTTP {updated_stats.status_code}")
        else:
            results.log_fail("Integration - Rate update", f"HTTP {update_response.status_code}")
        
        # 2. Generate PDF report and verify it contains updated configuration
        pdf_response = requests.post(f"{BASE_URL}/export-pdf", timeout=30)
        if pdf_response.status_code == 200:
            content_type = pdf_response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                results.log_pass("Integration - PDF generation with updated configuration")
            else:
                results.log_fail("Integration - PDF generation", f"Expected PDF, got: {content_type}")
        else:
            results.log_fail("Integration - PDF generation", f"HTTP {pdf_response.status_code}")
        
        # 3. Restore original rates
        restore_response = requests.put(f"{BASE_URL}/commission-rates", json=original_rates, headers=HEADERS, timeout=10)
        if restore_response.status_code == 200:
            results.log_pass("Integration - Restore original configuration")
        else:
            results.log_fail("Integration - Restore config", f"HTTP {restore_response.status_code}")
        
        # Clean up test sale
        requests.delete(f"{BASE_URL}/sales/{created_sale['id']}", timeout=10)
        
    except Exception as e:
        results.log_fail("Integration scenarios", f"Exception: {str(e)}")

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
    
    # Run all test suites (existing + new features)
    test_sales_crud_operations(results)
    test_commission_calculation_engine(results)
    test_statistics_and_analytics_api(results)
    test_commission_configuration_management(results)
    
    # NEW FEATURE TESTS
    test_commission_settings_api(results)
    test_pdf_export_api(results)
    test_integration_scenarios(results)
    
    # Cleanup
    cleanup_test_data()
    
    # Final summary
    results.summary()
    
    # Return success status
    return results.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)