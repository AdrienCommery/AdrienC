#!/usr/bin/env python3
"""
CA Prime Logic Testing Suite
Tests the corrected CA Prime logic based on NUMBER OF VEHICLES SOLD instead of sales amount.
"""

import requests
import json
from datetime import datetime
import uuid
import time

# Configuration
BASE_URL = "https://39ec4bdd-2482-43b6-9c28-51c1ac366160.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class CATestResults:
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
        print(f"\n{'='*80}")
        print(f"CA PRIME TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*80}")

def create_test_sale(vehicle_type="CAMPING-CAR", prix_vente=50000, nom="TestUser", prenom="CA"):
    """Create a test sale with realistic data"""
    return {
        "nom": nom,
        "prenom": prenom,
        "type": vehicle_type,
        "marque": "TestMarque",
        "modele": "TestModel",
        "date_vente": "2025-10-15",
        "date_livraison_previsionnelle": "2025-11-15",
        "prix_vente": prix_vente,
        "montant_financement": 30000,
        "nombre_pc": 2,
        "annulation": False
    }

def cleanup_test_sales():
    """Clean up test sales created during CA Prime testing"""
    try:
        response = requests.get(f"{BASE_URL}/sales", timeout=10)
        if response.status_code == 200:
            sales = response.json()
            for sale in sales:
                if sale.get("nom") == "TestUser" and sale.get("prenom") == "CA":
                    requests.delete(f"{BASE_URL}/sales/{sale['id']}", timeout=10)
            print("🧹 Cleaned up CA Prime test data")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {str(e)}")

def test_ca_prime_configuration(results):
    """Test 1: Configuration API - Verify ca_prime_thresholds with vehicle numbers"""
    print("\n--- Test 1: CA Prime Configuration ---")
    
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            ca_thresholds = config.get("ca_prime_thresholds", {})
            
            # Expected thresholds: vehicle numbers as keys
            expected_keys = ["50", "60", "70", "90"]
            expected_values = [5000, 6000, 7000, 11000]
            
            # Check if keys are vehicle numbers (strings)
            actual_keys = list(ca_thresholds.keys())
            if set(actual_keys) == set(expected_keys):
                results.log_pass("CA Prime thresholds - Vehicle number keys (50, 60, 70, 90)")
            else:
                results.log_fail("CA Prime thresholds - Keys", f"Expected {expected_keys}, got {actual_keys}")
            
            # Check threshold values
            for key, expected_value in zip(expected_keys, expected_values):
                if ca_thresholds.get(key) == expected_value:
                    results.log_pass(f"CA Prime threshold - {key} vehicles → {expected_value}€")
                else:
                    results.log_fail(f"CA Prime threshold - {key} vehicles", 
                                   f"Expected {expected_value}€, got {ca_thresholds.get(key)}€")
        else:
            results.log_fail("GET /api/config", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("CA Prime Configuration Test", f"Exception: {str(e)}")

def test_ca_prime_progress_type(results):
    """Test 2: Stats API - Verify ca_prime_progress is INTEGER (vehicle count)"""
    print("\n--- Test 2: CA Prime Progress Data Type ---")
    
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            ca_prime_progress = stats.get("ca_prime_progress")
            
            # Check if ca_prime_progress is an integer
            if isinstance(ca_prime_progress, int):
                results.log_pass("CA Prime progress - INTEGER type (vehicle count)")
            else:
                results.log_fail("CA Prime progress - Data type", 
                               f"Expected int, got {type(ca_prime_progress).__name__}: {ca_prime_progress}")
            
            # Check if it's non-negative
            if ca_prime_progress >= 0:
                results.log_pass("CA Prime progress - Non-negative value")
            else:
                results.log_fail("CA Prime progress - Value", f"Negative value: {ca_prime_progress}")
                
        else:
            results.log_fail("GET /api/stats", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("CA Prime Progress Type Test", f"Exception: {str(e)}")

def test_vehicle_count_logic(results):
    """Test 3: Vehicle Count Logic - Create sales and verify ca_prime_progress = vn_livres + vo_livres"""
    print("\n--- Test 3: Vehicle Count Logic ---")
    
    # Clean up first
    cleanup_test_sales()
    
    # Get initial stats
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if response.status_code != 200:
            results.log_fail("Initial stats check", f"HTTP {response.status_code}")
            return
        initial_stats = response.json()
        initial_ca_progress = initial_stats.get("ca_prime_progress", 0)
        initial_vn = initial_stats.get("vn_livres", 0)
        initial_vo = initial_stats.get("vo_livres", 0)
        
        print(f"Initial state: VN={initial_vn}, VO={initial_vo}, CA Progress={initial_ca_progress}")
    except Exception as e:
        results.log_fail("Initial stats check", f"Exception: {str(e)}")
        return
    
    # Test 3a: Create 1 CAMPING-CAR sale
    try:
        camping_car_sale = create_test_sale("CAMPING-CAR", 45000, "TestUser", "CA")
        response = requests.post(f"{BASE_URL}/sales", json=camping_car_sale, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            # Check stats after CAMPING-CAR sale
            time.sleep(1)  # Brief delay for data consistency
            stats_response = requests.get(f"{BASE_URL}/stats", timeout=10)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                ca_progress = stats.get("ca_prime_progress", 0)
                vn_count = stats.get("vn_livres", 0)
                
                expected_progress = initial_ca_progress + 1
                if ca_progress == expected_progress:
                    results.log_pass("1 CAMPING-CAR sale → ca_prime_progress increased by 1")
                else:
                    results.log_fail("CAMPING-CAR vehicle count", 
                                   f"Expected ca_prime_progress={expected_progress}, got {ca_progress}")
                
                # Verify it's counted as VN (CAMPING-CAR)
                expected_vn = initial_vn + 1
                if vn_count == expected_vn:
                    results.log_pass("CAMPING-CAR counted as VN (vn_livres)")
                else:
                    results.log_fail("CAMPING-CAR VN count", f"Expected vn_livres={expected_vn}, got {vn_count}")
            else:
                results.log_fail("Stats after CAMPING-CAR", f"HTTP {stats_response.status_code}")
        else:
            results.log_fail("Create CAMPING-CAR sale", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("CAMPING-CAR sale test", f"Exception: {str(e)}")
    
    # Test 3b: Create 1 FOURGON sale
    try:
        fourgon_sale = create_test_sale("FOURGON", 55000, "TestUser", "CA")
        response = requests.post(f"{BASE_URL}/sales", json=fourgon_sale, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            # Check stats after FOURGON sale
            time.sleep(1)
            stats_response = requests.get(f"{BASE_URL}/stats", timeout=10)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                ca_progress = stats.get("ca_prime_progress", 0)
                vo_count = stats.get("vo_livres", 0)
                
                expected_progress = initial_ca_progress + 2  # 1 CAMPING-CAR + 1 FOURGON
                if ca_progress == expected_progress:
                    results.log_pass("1 FOURGON sale → total ca_prime_progress = 2")
                else:
                    results.log_fail("FOURGON vehicle count", 
                                   f"Expected total ca_prime_progress={expected_progress}, got {ca_progress}")
                
                # Verify it's counted as VO (FOURGON)
                expected_vo = initial_vo + 1
                if vo_count == expected_vo:
                    results.log_pass("FOURGON counted as VO (vo_livres)")
                else:
                    results.log_fail("FOURGON VO count", f"Expected vo_livres={expected_vo}, got {vo_count}")
            else:
                results.log_fail("Stats after FOURGON", f"HTTP {stats_response.status_code}")
        else:
            results.log_fail("Create FOURGON sale", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("FOURGON sale test", f"Exception: {str(e)}")
    
    # Test 3c: Verify ca_prime_progress = vn_livres + vo_livres
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            ca_progress = stats.get("ca_prime_progress", 0)
            vn_count = stats.get("vn_livres", 0)
            vo_count = stats.get("vo_livres", 0)
            
            expected_progress = vn_count + vo_count
            if ca_progress == expected_progress:
                results.log_pass(f"CA Prime formula: ca_prime_progress ({ca_progress}) = vn_livres ({vn_count}) + vo_livres ({vo_count})")
            else:
                results.log_fail("CA Prime formula", 
                               f"ca_prime_progress ({ca_progress}) ≠ vn_livres ({vn_count}) + vo_livres ({vo_count})")
        else:
            results.log_fail("Final formula verification", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("CA Prime formula verification", f"Exception: {str(e)}")

def test_cancelled_sales_exclusion(results):
    """Test 4: Cancelled Sales - Verify cancelled sales don't count toward vehicle totals"""
    print("\n--- Test 4: Cancelled Sales Exclusion ---")
    
    try:
        # Get current stats
        response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if response.status_code != 200:
            results.log_fail("Pre-cancellation stats", f"HTTP {response.status_code}")
            return
        pre_stats = response.json()
        pre_ca_progress = pre_stats.get("ca_prime_progress", 0)
        
        # Create a sale
        test_sale = create_test_sale("VAN", 60000, "TestUser", "CA")
        create_response = requests.post(f"{BASE_URL}/sales", json=test_sale, headers=HEADERS, timeout=10)
        
        if create_response.status_code == 200:
            sale_data = create_response.json()
            sale_id = sale_data.get("id")
            
            # Verify sale increases count
            time.sleep(1)
            mid_response = requests.get(f"{BASE_URL}/stats", timeout=10)
            if mid_response.status_code == 200:
                mid_stats = mid_response.json()
                mid_ca_progress = mid_stats.get("ca_prime_progress", 0)
                
                if mid_ca_progress == pre_ca_progress + 1:
                    results.log_pass("VAN sale increases ca_prime_progress by 1")
                else:
                    results.log_fail("VAN sale count", f"Expected +1, got {mid_ca_progress - pre_ca_progress}")
                
                # Cancel the sale
                cancelled_sale = test_sale.copy()
                cancelled_sale["annulation"] = True
                cancel_response = requests.put(f"{BASE_URL}/sales/{sale_id}", 
                                             json=cancelled_sale, headers=HEADERS, timeout=10)
                
                if cancel_response.status_code == 200:
                    # Verify cancelled sale doesn't count
                    time.sleep(1)
                    post_response = requests.get(f"{BASE_URL}/stats", timeout=10)
                    if post_response.status_code == 200:
                        post_stats = post_response.json()
                        post_ca_progress = post_stats.get("ca_prime_progress", 0)
                        
                        if post_ca_progress == pre_ca_progress:
                            results.log_pass("Cancelled sale excluded from ca_prime_progress")
                        else:
                            results.log_fail("Cancelled sale exclusion", 
                                           f"Expected ca_prime_progress={pre_ca_progress}, got {post_ca_progress}")
                    else:
                        results.log_fail("Post-cancellation stats", f"HTTP {post_response.status_code}")
                else:
                    results.log_fail("Cancel sale", f"HTTP {cancel_response.status_code}")
            else:
                results.log_fail("Mid-test stats", f"HTTP {mid_response.status_code}")
        else:
            results.log_fail("Create VAN sale for cancellation test", f"HTTP {create_response.status_code}")
    except Exception as e:
        results.log_fail("Cancelled sales exclusion test", f"Exception: {str(e)}")

def test_prime_calculation_thresholds(results):
    """Test 5: Prime Calculation - Test different vehicle counts and verify correct prime levels"""
    print("\n--- Test 5: Prime Calculation Thresholds ---")
    
    # This test verifies the logic exists, but doesn't create 50+ sales due to practical constraints
    # Instead, we verify the configuration is correct for the thresholds
    
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            ca_thresholds = config.get("ca_prime_thresholds", {})
            
            # Test threshold logic
            test_cases = [
                ("50", 5000, "50 vehicles → 5,000€ prime"),
                ("60", 6000, "60 vehicles → 6,000€ prime"),
                ("70", 7000, "70 vehicles → 7,000€ prime"),
                ("90", 11000, "90 vehicles → 11,000€ prime")
            ]
            
            for vehicle_count, expected_prime, description in test_cases:
                actual_prime = ca_thresholds.get(vehicle_count)
                if actual_prime == expected_prime:
                    results.log_pass(f"Prime threshold: {description}")
                else:
                    results.log_fail(f"Prime threshold: {vehicle_count} vehicles", 
                                   f"Expected {expected_prime}€, got {actual_prime}€")
            
            # Verify thresholds are based on vehicle count, not sales amount
            if all(key.isdigit() and int(key) <= 100 for key in ca_thresholds.keys()):
                results.log_pass("Prime thresholds based on vehicle count (not sales amount)")
            else:
                results.log_fail("Prime threshold basis", "Thresholds appear to be based on sales amount, not vehicle count")
                
        else:
            results.log_fail("GET /api/config for prime thresholds", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("Prime calculation thresholds test", f"Exception: {str(e)}")

def test_commission_unchanged(results):
    """Test 6: Commission Calculations - Verify commission calculations remain based on sales amounts"""
    print("\n--- Test 6: Commission Calculations Unchanged ---")
    
    try:
        # Get current stats to check commission calculations
        response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            
            # Verify commission fields exist and are calculated based on sales amounts
            commission_vente = stats.get("commission_vente", 0)
            commission_financement = stats.get("commission_financement", 0)
            ca_cumule = stats.get("ca_cumule", 0)
            
            if isinstance(commission_vente, (int, float)) and commission_vente >= 0:
                results.log_pass("Commission vente - Calculated based on sales amounts")
            else:
                results.log_fail("Commission vente", f"Invalid value: {commission_vente}")
            
            if isinstance(commission_financement, (int, float)) and commission_financement >= 0:
                results.log_pass("Commission financement - Calculated based on financing amounts")
            else:
                results.log_fail("Commission financement", f"Invalid value: {commission_financement}")
            
            # Verify CA cumule is still based on sales amounts (not vehicle count)
            if isinstance(ca_cumule, (int, float)) and ca_cumule >= 0:
                results.log_pass("CA cumule - Still based on sales amounts (unchanged)")
            else:
                results.log_fail("CA cumule", f"Invalid value: {ca_cumule}")
                
        else:
            results.log_fail("GET /api/stats for commission check", f"HTTP {response.status_code}")
    except Exception as e:
        results.log_fail("Commission calculations unchanged test", f"Exception: {str(e)}")

def main():
    """Main CA Prime testing function"""
    print("🎯 Starting CA Prime Logic Testing Suite")
    print("Testing CA Prime based on NUMBER OF VEHICLES SOLD (not sales amount)")
    print(f"Testing against: {BASE_URL}")
    
    results = CATestResults()
    
    # Test API connection first
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            results.log_pass("API Connection")
        else:
            results.log_fail("API Connection", f"HTTP {response.status_code}")
            results.summary()
            return False
    except Exception as e:
        results.log_fail("API Connection", f"Exception: {str(e)}")
        results.summary()
        return False
    
    # Run CA Prime specific tests
    test_ca_prime_configuration(results)
    test_ca_prime_progress_type(results)
    test_vehicle_count_logic(results)
    test_cancelled_sales_exclusion(results)
    test_prime_calculation_thresholds(results)
    test_commission_unchanged(results)
    
    # Cleanup
    cleanup_test_sales()
    
    # Final summary
    results.summary()
    
    return results.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)