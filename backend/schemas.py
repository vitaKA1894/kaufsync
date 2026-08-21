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
    settings_push_async_events: Optional[bool] = None
    settings_push_new_items: Optional[bool] = None

# NEU: Für die Passwort-Änderung
class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    is_admin: Optional[bool] = False
    status: str
    settings_push_async_events: bool
    settings_push_new_items: bool

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    action_url: Optional[str] = None
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str

class LoginRequest(BaseModel):
    email: str
    password: str

# --- ITEM SCHEMAS ---
class ItemBase(BaseModel):
    name: str
    category: Optional[str] = "Sonstiges"
    quantity: float = 1.0
    unit: Optional[str] = "Stk"
    note: Optional[str] = None
    tags: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    quantity: Optional[float] = None
    note: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None

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

# --- ACTIVITY LOG SCHEMAS ---
class ActivityLogResponse(BaseModel):
    id: str
    list_id: str
    user_id: str
    action_type: str
    item_name: str
    created_at: datetime

    # Optional field for frontend display
    user_name: Optional[str] = None

    class Config:
        from_attributes = True

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