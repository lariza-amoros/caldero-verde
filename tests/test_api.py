import os
import unittest
from unittest.mock import patch

from app import create_app


class WriteProtectionTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"APP_ACCESS_PIN": "246810"})
        self.environment.start()
        self.app = create_app(client=object()).test_client()

    def tearDown(self):
        self.environment.stop()

    def test_write_requires_access_code(self):
        response = self.app.post("/api/inventory", json={})
        self.assertEqual(response.status_code, 401)

    def test_authorized_write_still_validates_payload(self):
        response = self.app.post(
            "/api/inventory",
            json={},
            headers={"X-Caldero-Pin": "246810"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
