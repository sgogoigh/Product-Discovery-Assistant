import pytest
from fastapi.testclient import TestClient
from app.main import app   # adjust import if your FastAPI app is elsewhere

client = TestClient(app)

# --- Fixtures ---
@pytest.fixture
def sample_product():
    return {
        "title": "Test Skort",
        "price": 1999,
        "description": "Comfortable skort for testing",
        "category": "Skorts",
        "image_url": "https://hunnit.com/cdn/shop/products/skort.jpg",
        "source_url": "https://hunnit.com/products/test-skort",
        "features": [
            {"section": "Product Features", "title": "Soft Fabric", "description": "Feels great"},
            {"section": "Function", "title": "Workout Ready", "description": "Perfect for cardio"}
        ]
    }

# --- Tests ---
def test_create_product(sample_product):
    response = client.post("/api/products/", json=sample_product)
    assert response.status_code == 201
    data = response.json()
    assert "product_id" in data
    assert data["title"] == sample_product["title"]

def test_get_products():
    response = client.get("/api/products/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_product_by_id(sample_product):
    # Create first
    create_resp = client.post("/api/products/", json=sample_product)
    product_id = create_resp.json()["product_id"]

    # Fetch
    response = client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == product_id

def test_update_product(sample_product):
    # Create
    create_resp = client.post("/api/products/", json=sample_product)
    product_id = create_resp.json()["product_id"]

    # Update
    updated = {**sample_product, "title": "Updated Skort"}
    response = client.put(f"/api/products/{product_id}", json=updated)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Skort"

def test_patch_product(sample_product):
    # Create
    create_resp = client.post("/api/products/", json=sample_product)
    product_id = create_resp.json()["product_id"]

    # Patch only price
    response = client.patch(f"/api/products/{product_id}", json={"price": 0})
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 0
    assert data["title"] == sample_product["title"]  # unchanged

def test_delete_product(sample_product):
    # Create
    create_resp = client.post("/api/products/", json=sample_product)
    product_id = create_resp.json()["product_id"]

    # Delete
    response = client.delete(f"/api/products/{product_id}")
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/api/products/{product_id}")
    assert response.status_code == 404

def test_invalid_post():
    bad_product = {
        "title": "Bad Product",
        "price": "cheap",  # invalid type
        "category": "Skorts"
    }
    response = client.post("/api/products/", json=bad_product)
    assert response.status_code == 422