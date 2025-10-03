import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_users_endpoint(self):
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_upload_clothes_endpoint(self):
        with open("path/to/sample_clothing_image.jpg", "rb") as image_file:
            response = self.client.post("/api/clothes/upload", files={"file": image_file})
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())

    def test_recommendation_endpoint(self):
        response = self.client.get("/api/recommendation")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

if __name__ == "__main__":
    unittest.main()