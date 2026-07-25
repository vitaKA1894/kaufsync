from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    email: str
    password: str
    display_name: str

# NEU: Für das Profil-Update
class UserUpdate(BaseModel):
    display_name: str

# NEU: Für die Passwort-Änderung
class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

# --- ITEM SCHEMAS ---
class ItemBase(BaseModel):
    name: str
    category: Optional[str] = "Allgemein"
    quantity: float = 1.0
    unit: Optional[str] = "Stk"
    note: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    status: Optional[str] = None
    quantity: Optional[float] = None
    note: Optional[str] = None

class ItemUpdate(BaseModel):
    status: Optional[str] = None
    quantity: Optional[float] = None
    note: Optional[str] = None
    category: Optional[str] = None

class ItemResponse(ItemBase):
    id: str
    list_id: str
    status: str
    # Hinweis: updated_at wurde entfernt, da es in models.Item nicht definiert war!
    
    class Config:
        from_attributes = True

# --- LIST SCHEMAS ---
class ListBase(BaseModel):
    name: str
    icon_name: Optional[str] = "mdi-cart"

class ListCreate(ListBase):
    pass

class ListResponse(ListBase):
    id: str
    created_at: datetime
    created_by: str
    share_code: str
    members: List[UserResponse] = []
    creator: Optional[UserResponse] = None
    items: List[ItemResponse] = []  # KORRIGIERT: List statt ListType
    
    class Config:
        from_attributes = True

# --- JOIN LIST SCHEMAS ---
class JoinListRequest(BaseModel):
    share_code: str

# --- INVITATION SCHEMAS ---
class InviteUserRequest(BaseModel):
    invitee_id: str

class ListInvitationResponse(BaseModel):
    id: str
    list_id: str
    inviter_id: str
    invitee_id: str
    status: str
    created_at: datetime

    # Optional fields for frontend display
    list_name: Optional[str] = None
    inviter_name: Optional[str] = None

    class Config:
        from_attributes = True