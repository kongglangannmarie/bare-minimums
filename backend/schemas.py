from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class IngredientBase(BaseModel):
    # Field names must exactly match the database columns
    category_id: int 
    supplier_id: Optional[int] = None
    ingredient_name: str
    quantity: float 
    unit_of_measurement: str
    low_stock_threshold: float
    is_active: bool = True
    
class IngredientCreate(IngredientBase):
    user_id: int

class IngredientUpdate(BaseModel):
    quantity: Optional[float] = None
    is_active: Optional[bool] = None

class IngredientResponse(IngredientBase):
    ingredient_id: int
    user_id: int
    last_updated: Optional[datetime] = None

    model_config = {"from_attributes": True}

# Supplier models remain the same...
class SupplierBase(BaseModel):
    supplier_name: str
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None 

class SupplierCreate(SupplierBase):
    user_id: int 

class SupplierResponse(SupplierBase):
    supplier_id: int
    user_id: int

    # Modern Pydantic V2 syntax
    model_config = {"from_attributes": True}
        