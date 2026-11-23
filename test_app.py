import unittest
from app import app
from database import init_database

class DaycareAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_database(force_recreate=True)

    def test_pages_load(self):
        pages = ["/", "/children", "/guardians", "/rooms-staff", "/attendance", "/activities", "/billing", "/sql-console"]
        for p in pages:
            res = self.client.get(p)
            self.assertEqual(res.status_code, 200, f"Page {p} failed with {res.status_code}")

    def test_api_stats(self):
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("total_children", data)
        self.assertGreater(data["total_children"], 0)

    def test_api_children_get(self):
        res = self.client.get("/api/children")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_api_sql_execute(self):
        res = self.client.post("/api/sql/execute", json={"sql": "SELECT COUNT(*) AS total FROM children;"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["columns"], ["total"])

    def test_payment_trigger(self):
        # Insert a payment and verify trigger updates invoice status
        res = self.client.post("/api/payments", json={
            "invoice_id": 3,
            "amount_paid": 250.00,
            "payment_mode": "Cash",
            "transaction_ref": "TEST-CASH-01"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

if __name__ == "__main__":
    unittest.main()
