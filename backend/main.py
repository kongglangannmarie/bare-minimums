from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt

from database import supabase
from schemas import (
    IngredientCreate, IngredientResponse, IngredientUpdate, 
    SupplierCreate, SupplierResponse, # Add these back!
    UserCreate, Token  
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

# --- AUTHENTICATION CONFIG ---
SECRET_KEY = "your-super-secret-key" # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- AUTH HELPER FUNCTIONS ---
def get_password_hash(password: str):
    # bcrypt requires passwords to be converted to bytes
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    # Convert back to a string so it can be saved in the database
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    pwd_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# --- AUTH ROUTES ---

@app.post("/register")
async def register(user: UserCreate):
    # 1. Check if email exists
    existing = supabase.table("users").select("*").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Hash password and save to DB
    hashed_password = get_password_hash(user.password)
    new_user = {
        "email": user.email,
        "password_hash": hashed_password,
        "business_name": user.business_name
    }
    supabase.table("users").insert(new_user).execute()
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2 uses "username" for the identifier (we will map it to email)
    response = supabase.table("users").select("*").eq("email", form_data.username).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    user = response.data[0]
    
    # Verify the hashed password
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Issue a token using their user_id
    access_token = create_access_token(data={"sub": str(user["user_id"])})
    return {"access_token": access_token, "token_type": "bearer"}


# --- INVENTORY ROUTES ---

@app.get("/ingredients/", response_model=List[IngredientResponse])
async def get_inventory(current_user_id: int = Depends(get_current_user)):
    response = supabase.table("ingredients").select("*").eq("user_id", current_user_id).execute()
    return response.data

@app.post("/ingredients/", response_model=IngredientResponse)
async def add_ingredient(item: IngredientCreate, current_user_id: int = Depends(get_current_user)):
    item_data = item.model_dump()
    item_data["user_id"] = current_user_id  
    
    # 1. Insert the new ingredient
    response = supabase.table("ingredients").insert(item_data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Error adding item")
        
    new_item = response.data[0]
    
    # 2. Log the initial stock as a transaction
    if new_item["quantity"] > 0:
        transaction_data = {
            "ingredient_id": new_item["ingredient_id"],
            "change_amount": new_item["quantity"],
            "change_type": "Restock" # Updated to match your schema
        }
        supabase.table("inventory_transactions").insert(transaction_data).execute()
        
    return new_item

@app.patch("/ingredients/{item_id}", response_model=IngredientResponse)
async def update_ingredient(item_id: int, updates: IngredientUpdate, current_user_id: int = Depends(get_current_user)):
    # 1. Fetch the current item
    existing_item_res = supabase.table("ingredients").select("*") \
        .eq("ingredient_id", item_id) \
        .eq("user_id", current_user_id) \
        .execute()
        
    if not existing_item_res.data:
        raise HTTPException(status_code=404, detail="Item not found or you don't have permission to edit it")
        
    old_item = existing_item_res.data[0]
    
    # 2. Perform the update
    response = supabase.table("ingredients").update(updates.model_dump(exclude_unset=True)) \
        .eq("ingredient_id", item_id) \
        .eq("user_id", current_user_id) \
        .execute()
        
    updated_item = response.data[0]
    
    # 3. Calculate difference and log transaction
    if updates.quantity is not None:
        old_qty = old_item["quantity"]
        new_qty = updates.quantity
        change_amount = new_qty - old_qty
        
        if change_amount != 0:
            # Determine type based on your schema's exact values
            tx_type = "Restock" if change_amount > 0 else "Used"
            
            transaction_data = {
                "ingredient_id": item_id,
                "change_amount": change_amount,
                "change_type": tx_type
            }
            supabase.table("inventory_transactions").insert(transaction_data).execute()

    return updated_item

@app.delete("/ingredients/{item_id}")
async def delete_item(item_id: int, current_user_id: int = Depends(get_current_user)):
    # Ensure they own the item they are trying to delete
    response = supabase.table("ingredients").delete() \
        .eq("ingredient_id", item_id) \
        .eq("user_id", current_user_id) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=404, detail="Item not found or you don't have permission to delete it")
    return {"status": "deleted"}

# --- SUPPLIER ROUTES ---

@app.get("/suppliers/", response_model=List[SupplierResponse])
async def get_suppliers(current_user_id: int = Depends(get_current_user)):
    response = supabase.table("suppliers").select("*").eq("user_id", current_user_id).execute()
    return response.data

@app.post("/suppliers/", response_model=SupplierResponse)
async def add_supplier(supplier: SupplierCreate, current_user_id: int = Depends(get_current_user)):
    supplier_data = supplier.model_dump()
    supplier_data["user_id"] = current_user_id # Force the user_id to be the logged-in user
    
    response = supabase.table("suppliers").insert(supplier_data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Error adding supplier")
    return response.data[0]

# --- ALERTS ---

@app.get("/alerts/")
async def get_low_stock_alerts(current_user_id: int = Depends(get_current_user)):
    response = supabase.table("ingredients").select("*").eq("user_id", current_user_id).execute()
    alerts = [
        item for item in response.data 
        if item['quantity'] <= item['low_stock_threshold'] 
    ]
    return {"alert_count": len(alerts), "items": alerts}
