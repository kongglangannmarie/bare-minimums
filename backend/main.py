from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import supabase
from schemas import (
    IngredientCreate, IngredientResponse, IngredientUpdate, 
    SupplierCreate, SupplierResponse
)
from typing import List

app = FastAPI(title="Bare Minimums API")

# Allows your local HTML file to communicate with this backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Inventory API is live"}

# --- INVENTORY ROUTES ---

@app.get("/ingredients/{user_id}", response_model=List[IngredientResponse])
async def get_inventory(user_id: int):
    response = supabase.table("ingredients").select("*").eq("user_id", user_id).execute()
    return response.data

@app.post("/ingredients/", response_model=IngredientResponse)
async def add_ingredient(item: IngredientCreate):
    # Change item.dict() to item.model_dump()
    response = supabase.table("ingredients").insert(item.model_dump()).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Error adding item")
    return response.data[0]

@app.patch("/ingredients/{item_id}", response_model=IngredientResponse)
async def update_ingredient(item_id: int, updates: IngredientUpdate):
    # Change updates.dict(...) to updates.model_dump(...)
    response = supabase.table("ingredients").update(updates.model_dump(exclude_unset=True)).eq("ingredient_id", item_id).execute()
    return response.data[0]

@app.delete("/ingredients/{item_id}")
async def delete_item(item_id: int):
    supabase.table("ingredients").delete().eq("ingredient_id", item_id).execute()
    return {"status": "deleted"}

# --- SUPPLIER ROUTES ---

@app.get("/suppliers/{user_id}", response_model=List[SupplierResponse])
async def get_suppliers(user_id: int):
    response = supabase.table("suppliers").select("*").eq("user_id", user_id).execute()
    return response.data

@app.post("/suppliers/", response_model=SupplierResponse)
async def add_supplier(supplier: SupplierCreate):
    response = supabase.table("suppliers").insert(supplier.model_dump()).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Error adding supplier")
    return response.data[0]

# --- ALERTS ---
@app.get("/alerts/{user_id}")
async def get_low_stock_alerts(user_id: int):
    response = supabase.table("ingredients").select("*").eq("user_id", user_id).execute()
    alerts = [
        item for item in response.data 
        if item['quantity'] <= item['low_stock_threshold'] # Updated column names
    ]
    return {"alert_count": len(alerts), "items": alerts}
