from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

TEST_USER_ID = 999 
test_item_id = None 

def test_api_is_live():
    response = client.get("/")
    assert response.status_code == 200

def test_add_ingredient():
    global test_item_id
    
    # Update the test data to match the new schema
    new_item = {
        "user_id": TEST_USER_ID,
        "category_id": 1, # Make sure a category with ID 1 exists in your DB!
        "ingredient_name": "Test Burger Buns",
        "quantity": 20.0,
        "unit_of_measurement": "packs",
        "low_stock_threshold": 10.0,
        "is_active": True
    }
    
    response = client.post("/ingredients/", json=new_item)
    assert response.status_code == 200, f"Error: {response.text}"
    
    data = response.json()
    assert data["ingredient_name"] == "Test Burger Buns"
    
    # Supabase uses 'ingredient_id' not 'id'
    test_item_id = data["ingredient_id"] 

def test_update_ingredient_quantity():
    global test_item_id
    
    update_data = {
        "quantity": 8
    }
    
    # Notice we removed the 'status' column because it's not in the DB schema
    response = client.patch(f"/ingredients/{test_item_id}", json=update_data)
    assert response.status_code == 200, f"Error: {response.text}"

def test_automated_alerts_logic():
    response = client.get(f"/alerts/{TEST_USER_ID}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["alert_count"] >= 1

def test_delete_ingredient():
    global test_item_id
    
    response = client.delete(f"/ingredients/{test_item_id}")
    assert response.status_code == 200
    