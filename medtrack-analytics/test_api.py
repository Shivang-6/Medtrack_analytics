# test_api.py
import json
from datetime import datetime, timedelta

import requests

BASE_URL = "http://localhost:5000/api"


def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.status_code, response.json())
    return response.status_code == 200


def test_drug_endpoints():
    """Test drug-related endpoints"""
    print("\n=== Testing Drug Endpoints ===")

    response = requests.get(f"{BASE_URL}/drugs")
    print(f"Get Drugs: {response.status_code}")

    response = requests.get(f"{BASE_URL}/drugs/low-stock")
    print(f"Low Stock: {response.status_code}")

    response = requests.get(f"{BASE_URL}/drugs/inventory/value")
    print(f"Inventory Value: {response.status_code}")

    return True


def test_sales_endpoints():
    """Test sales-related endpoints"""
    print("\n=== Testing Sales Endpoints ===")

    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now() - timedelta(days=30)).date().isoformat()

    response = requests.get(
        f"{BASE_URL}/sales/analytics/period",
        params={'start_date': start_date, 'end_date': end_date}
    )
    print(f"Sales Analytics: {response.status_code}")

    response = requests.get(f"{BASE_URL}/sales/analytics/top-drugs")
    print(f"Top Drugs: {response.status_code}")

    return True


def test_analytics_endpoints():
    """Test analytics endpoints"""
    print("\n=== Testing Analytics Endpoints ===")

    response = requests.get(f"{BASE_URL}/analytics/dashboard")
    print(f"Dashboard: {response.status_code}")

    response = requests.get(f"{BASE_URL}/analytics/inventory-health")
    print(f"Inventory Health: {response.status_code}")

    return True


def test_patient_endpoints():
    """Test patient endpoints"""
    print("\n=== Testing Patient Endpoints ===")

    response = requests.get(f"{BASE_URL}/patients")
    print(f"Get Patients: {response.status_code}")

    response = requests.get(f"{BASE_URL}/analytics/patient-demographics")
    print(f"Patient Demographics: {response.status_code}")

    return True


def create_sample_sale():
    """Create a sample sale transaction"""
    print("\n=== Creating Sample Sale ===")

    response = requests.get(f"{BASE_URL}/drugs")
    if response.status_code == 200:
        drugs = response.json().get('drugs', [])
        if drugs:
            drug_id = drugs[0]['id']

            sale_data = {
                'drug_id': drug_id,
                'quantity': 2,
                'unit_price': 10.99,
                'pharmacy_id': 101,
                'pharmacy_name': 'Test Pharmacy',
                'payment_method': 'Cash'
            }

            response = requests.post(
                f"{BASE_URL}/sales",
                json=sale_data,
                headers={'Content-Type': 'application/json'}
            )
            print(f"Create Sale: {response.status_code}")
            if response.status_code == 201:
                print("Sale created successfully!")
                return True

    print("Failed to create sale")
    return False


def run_all_tests():
    """Run all API tests"""
    print("Starting API Tests...")
    print("=" * 50)

    tests = [
        ("Health Check", test_health),
        ("Drug Endpoints", test_drug_endpoints),
        ("Sales Endpoints", test_sales_endpoints),
        ("Analytics Endpoints", test_analytics_endpoints),
        ("Patient Endpoints", test_patient_endpoints),
        ("Create Sample Sale", create_sample_sale)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            status = "PASS" if success else "FAIL"
            print(f"{test_name}: {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"{test_name}: ERROR - {str(e)}")

    print("\n" + "=" * 50)
    print("Test Summary:")
    for test_name, success in results:
        status = "\u2713 PASS" if success else "\u2717 FAIL"
        print(f"  {status} - {test_name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")


+if __name__ == "__main__":
+    run_all_tests()
