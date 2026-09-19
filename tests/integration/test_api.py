#!/usr/bin/env python3
"""
API Test Script - Verify endpoints work with seeded data
"""
import requests
import json
from typing import Dict, Optional

BASE_URL = "http://localhost:8000/api/v1"

class APITester:
    def __init__(self):
        self.tokens = {}
        self.session = requests.Session()
    
    def login(self, email: str, password: str, role: str) -> bool:
        """Login and store token"""
        print(f"\n🔑 Logging in as {role}: {email}")
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                data={"username": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[role] = data['access_token']
                print(f"  ✓ Login successful")
                return True
            else:
                print(f"  ✗ Login failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def get_headers(self, role: str) -> Dict:
        """Get authorization headers"""
        if role not in self.tokens:
            return {"Content-Type": "application/json"}
        return {"Authorization": f"Bearer {self.tokens[role]}"}
    
    def test_endpoint(self, method: str, endpoint: str, role: str, 
                     data: Optional[Dict] = None, expected_status: int = 200) -> bool:
        """Test an endpoint"""
        url = f"{BASE_URL}{endpoint}"
        headers = self.get_headers(role)
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            else:
                return False
            
            success = response.status_code == expected_status
            status_icon = "✓" if success else "✗"
            print(f"  {status_icon} {method:5} {endpoint:40} → {response.status_code}")
            
            if not success:
                try:
                    print(f"      Response: {response.json()}")
                except:
                    print(f"      Response: {response.text[:100]}")
            
            return success
        except Exception as e:
            print(f"  ✗ {method:5} {endpoint:40} → Error: {e}")
            return False

def main():
    tester = APITester()
    
    print("="*80)
    print("🧪 FREELANCE PLATFORM API TEST SUITE")
    print("="*80)
    print("\nNote: API must be running on localhost:8000")
    print("Start API with: python -m uvicorn app.main:app --reload")
    
    # ========== AUTHENTICATION ==========
    print("\n" + "="*80)
    print("1️⃣  AUTHENTICATION")
    print("="*80)
    
    tester.login("admin1@freelance.example.com", "admin1pass", "ADMIN")
    tester.login("client1@freelance.example.com", "client1pass", "CLIENT")
    tester.login("freelancer1@freelance.example.com", "freelancer1pass", "FREELANCER")
    
    if not tester.tokens:
        print("\n❌ No successful logins - API may not be running")
        print("   Start API: cd /home/shadow-66/freelance_back")
        print("   Then run: source .venv/bin/activate && python -m uvicorn app.main:app --reload")
        return
    
    # ========== ADMIN ENDPOINTS ==========
    print("\n" + "="*80)
    print("2️⃣  ADMIN ENDPOINTS")
    print("="*80)
    
    tester.test_endpoint("GET", "/admin/stats", "ADMIN")
    tester.test_endpoint("GET", "/admin/audit-logs?skip=0&limit=10", "ADMIN")
    tester.test_endpoint("GET", "/admin/system-warnings?skip=0&limit=10", "ADMIN")
    tester.test_endpoint("GET", "/admin/feedbacks/pending", "ADMIN")
    tester.test_endpoint("GET", "/admin/categories", "ADMIN")
    
    # ========== CLIENT ENDPOINTS ==========
    print("\n" + "="*80)
    print("3️⃣  CLIENT ENDPOINTS")
    print("="*80)
    
    tester.test_endpoint("GET", "/client/projects", "CLIENT")
    tester.test_endpoint("GET", "/client/proposals", "CLIENT")
    tester.test_endpoint("GET", "/client/feedback/my-tickets", "CLIENT")
    
    # ========== FREELANCER ENDPOINTS ==========
    print("\n" + "="*80)
    print("4️⃣  FREELANCER ENDPOINTS")
    print("="*80)
    
    tester.test_endpoint("GET", "/freelance/projects", "FREELANCER")
    tester.test_endpoint("GET", "/freelance/proposals", "FREELANCER")
    
    # ========== USER ENDPOINTS ==========
    print("\n" + "="*80)
    print("5️⃣  USER ENDPOINTS")
    print("="*80)
    
    tester.test_endpoint("GET", "/users/me", "ADMIN")
    tester.test_endpoint("GET", "/users/me", "CLIENT")
    tester.test_endpoint("GET", "/users/me", "FREELANCER")
    
    # ========== SUMMARY ==========
    print("\n" + "="*80)
    print("✅ TEST SUMMARY")
    print("="*80)
    print("""
If most endpoints returned 200, the API is working correctly!

🚀 To run the actual server:
   cd /home/shadow-66/freelance_back
   source .venv/bin/activate
   python -m uvicorn app.main:app --reload

📝 Database credentials:
   Database: freelance.db (SQLite)
   Users created: 9 (3 per role)
   Test data: 83 total records

🔑 Test Credentials:
   Admin:      admin1@freelance.local / admin1pass
   Client:     client1@freelance.local / client1pass
   Freelancer: freelancer1@freelance.local / freelancer1pass
    """)
    print("="*80)

if __name__ == "__main__":
    main()
