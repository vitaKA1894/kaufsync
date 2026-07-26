from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from datetime import timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models, schemas, auth
from database import engine, get_db

# Erstellt alle Tabellen in der Datenbank
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="KaufSync API", version="1.0.0")

# --- CORS KONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Erlaubt Anfragen vom Vue-Dev-Server
    allow_credentials=True,
    allow_methods=["*"],  # Erlaubt alle Methoden (GET, POST, etc.)
    allow_headers=["*"],  # Erlaubt alle Header
)

# --- WEBSOCKET MANAGER ---
class ConnectionManager:
    def __init__(self):
        # Speichert aktive Verbindungen pro Einkaufsliste (list_id)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, list_id: str):
        await websocket.accept()
        if list_id not in self.active_connections:
            self.active_connections[list_id] = []
        self.active_connections[list_id].append(websocket)

    def disconnect(self, websocket: WebSocket, list_id: str):
        if list_id in self.active_connections:
            self.active_connections[list_id].remove(websocket)

    async def broadcast(self, list_id: str, message: dict):
        if list_id in self.active_connections:
            for connection in self.active_connections[list_id]:
                await connection.send_json(message)

manager = ConnectionManager()

# --- WEBSOCKET ENDPUNKT ---
@app.websocket("/ws/{list_id}")
async def websocket_endpoint(websocket: WebSocket, list_id: str):
    await manager.connect(websocket, list_id)
    try:
        while True:
            # Wir halten die Verbindung offen und warten auf Disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, list_id)

# --- REST ENDPUNKTE ---
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "KaufSync Backend läuft!"}
    
# --- AUTHENTIFIZIERUNG ---

@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Prüfen ob Email schon existiert
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-Mail bereits registriert")
        
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email, 
        password_hash=hashed_password, 
        display_name=user_data.display_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login")
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    # User suchen
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not auth.verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Falsche E-Mail oder Passwort")
    
    # Token generieren
    access_token = auth.create_access_token(
        data={"sub": user.id}, 
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # NEU: Token direkt als JSON zurückgeben (nicht als Cookie)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.display_name}
    }
# --- USER ENDPUNKTE ---

class UserUpdate(schemas.BaseModel):
    display_name: str

class PasswordUpdate(schemas.BaseModel):
    old_password: str
    new_password: str

@app.get("/api/users/search", response_model=list[schemas.UserResponse])
def search_users(
    q: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Sucht Benutzer nach E-Mail oder Anzeigename, exklusive dem aktuellen Benutzer."""
    if not q or len(q) < 2:
        return []

    search_term = f"%{q}%"
    users = db.query(models.User).filter(
        (models.User.id != current_user.id) &
        ((models.User.email.ilike(search_term)) | (models.User.display_name.ilike(search_term)))
    ).limit(10).all()

    return users

@app.get("/api/users/me", response_model=schemas.UserResponse)
def get_current_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    """Gibt die Profildaten des aktuell eingeloggten Nutzers zurück."""
    return current_user

@app.put("/api/users/me", response_model=schemas.UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Aktualisiert den Anzeigenamen des Nutzers."""
    current_user.display_name = user_update.display_name
    db.commit()
    db.refresh(current_user)
    return current_user

@app.put("/api/users/me/password")
def change_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Ändert das Passwort des Nutzers nach erfolgreicher Überprüfung des alten Passworts."""
    # Altes Passwort verifizieren
    if not auth.verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Das alte Passwort ist inkorrekt")
    
    # Neues Passwort hashen und speichern
    current_user.password_hash = auth.get_password_hash(password_data.new_password)
    db.commit()
    return {"status": "ok", "message": "Passwort erfolgreich geändert"}
    
# --- GESCHÜTZTE DATEN-ENDPUNKTE ---

@app.post("/api/lists", response_model=schemas.ListResponse)
def create_list(
    list_data: schemas.ListCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # SCHUTZ
):
    new_list = models.List(
        name=list_data.name, 
        icon_name=list_data.icon_name,
        created_by=current_user.id # Liste an User binden
    )
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list

@app.get("/api/lists", response_model=list[schemas.ListResponse])
def get_lists(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Lade Listen, die der User selbst erstellt hat ODER in die er eingeladen wurde
    return db.query(models.List).filter(
        (models.List.created_by == current_user.id) | 
        (models.List.members.any(id=current_user.id))
    ).all()

@app.get("/api/invitations", response_model=list[schemas.ListInvitationResponse])
def get_invitations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Gibt alle offenen Einladungen für den aktuellen Benutzer zurück."""
    invitations = db.query(models.ListInvitation).filter(
        models.ListInvitation.invitee_id == current_user.id,
        models.ListInvitation.status == "pending"
    ).all()

    # Optional fields anreichern
    for inv in invitations:
        inv.list_name = inv.list.name
        inv.inviter_name = inv.inviter.display_name

    return invitations

@app.delete("/api/lists/{list_id}")
def delete_list(
    list_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Liste nicht gefunden")
        
    # Nur der Ersteller darf die Liste komplett löschen
    if db_list.created_by != current_user.id:
        # Alternativ: Nur Mitgliedschaft aufheben
        if current_user in db_list.members:
            db_list.members.remove(current_user)
            db.commit()
            return {"status": "ok", "message": "Liste verlassen"}
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
        
    db.delete(db_list)
    db.commit()
    return {"status": "ok", "message": "Liste erfolgreich gelöscht"}
    
@app.post("/api/lists/join", response_model=schemas.ListResponse)
def join_list(
    join_data: schemas.JoinListRequest, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Liste anhand des Codes suchen (wir machen ihn uppercase zur Sicherheit)
    db_list = db.query(models.List).filter(models.List.share_code == join_data.share_code.upper()).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Ungültiger Einladungscode")
        
    # Prüfen ob man schon Mitglied oder sogar Besitzer ist
    if current_user.id == db_list.created_by or current_user in db_list.members:
        raise HTTPException(status_code=400, detail="Du bist bereits in dieser Liste")
        
    # User als Mitglied hinzufügen
    db_list.members.append(current_user)
    db.commit()
    db.refresh(db_list)
    return db_list

@app.post("/api/lists/{list_id}/invite", response_model=schemas.ListInvitationResponse)
def invite_user(
    list_id: str,
    invite_data: schemas.InviteUserRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Lädt einen Benutzer in eine Liste ein."""
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Liste nicht gefunden")

    # Nur Mitglieder oder Besitzer dürfen einladen
    if db_list.created_by != current_user.id and current_user not in db_list.members:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")

    invitee = db.query(models.User).filter(models.User.id == invite_data.invitee_id).first()
    if not invitee:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    # Prüfen, ob der Benutzer bereits Mitglied ist
    if invitee.id == db_list.created_by or invitee in db_list.members:
        raise HTTPException(status_code=400, detail="Benutzer ist bereits Mitglied dieser Liste")

    # Prüfen, ob es bereits eine offene Einladung gibt
    existing_invite = db.query(models.ListInvitation).filter(
        models.ListInvitation.list_id == list_id,
        models.ListInvitation.invitee_id == invitee.id,
        models.ListInvitation.status == "pending"
    ).first()

    if existing_invite:
        raise HTTPException(status_code=400, detail="Es gibt bereits eine offene Einladung für diesen Benutzer")

    new_invite = models.ListInvitation(
        list_id=list_id,
        inviter_id=current_user.id,
        invitee_id=invitee.id
    )

    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)

    new_invite.list_name = db_list.name
    new_invite.inviter_name = current_user.display_name

    return new_invite

@app.post("/api/invitations/{invite_id}/respond")
def respond_to_invitation(
    invite_id: str,
    action: str, # "accept" oder "decline"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Nimmt eine Einladung an oder lehnt sie ab."""
    invite = db.query(models.ListInvitation).filter(
        models.ListInvitation.id == invite_id,
        models.ListInvitation.invitee_id == current_user.id
    ).first()

    if not invite:
        raise HTTPException(status_code=404, detail="Einladung nicht gefunden")

    if invite.status != "pending":
        raise HTTPException(status_code=400, detail="Einladung wurde bereits beantwortet")

    if action == "accept":
        invite.status = "accepted"
        db_list = db.query(models.List).filter(models.List.id == invite.list_id).first()
        if db_list and current_user not in db_list.members:
            db_list.members.append(current_user)
    elif action == "decline":
        invite.status = "declined"
    else:
        raise HTTPException(status_code=400, detail="Ungültige Aktion")

    db.commit()
    return {"status": "ok", "message": f"Einladung {'angenommen' if action == 'accept' else 'abgelehnt'}"}

@app.post("/api/lists/{list_id}/items", response_model=schemas.ItemResponse)
async def create_item(
    list_id: str, 
    item_data: schemas.ItemCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # SCHUTZ
):
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Liste nicht gefunden")
        
    new_item = models.Item(
        list_id=list_id, name=item_data.name, category=item_data.category,
        quantity=item_data.quantity, unit=item_data.unit, note=item_data.note,
        tags=item_data.tags,
        last_modified_by=current_user.id # Item an User binden
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    # WEBSOCKET BROADCAST - Jetzt inklusive Kategorie
    await manager.broadcast(list_id, {
        "event": "ITEM_UPDATED",
        "payload": {
            "list_id": list_id,
            "item": { "id": new_item.id, "name": new_item.name, "status": new_item.status, "quantity": new_item.quantity, "unit": new_item.unit, "category": new_item.category, "tags": new_item.tags }
        }
    })
    
    return new_item

@app.put("/api/items/{item_id}", response_model=schemas.ItemResponse)
async def update_item(
    item_id: str, 
    item_data: schemas.ItemUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # SCHUTZ
):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item nicht gefunden")
    
    if item_data.status is not None: db_item.status = item_data.status
    if item_data.quantity is not None: db_item.quantity = item_data.quantity
    if item_data.note is not None: db_item.note = item_data.note
    if hasattr(item_data, 'category') and item_data.category is not None: db_item.category = item_data.category
    if hasattr(item_data, 'tags') and item_data.tags is not None: db_item.tags = item_data.tags
    
    db_item.last_modified_by = current_user.id # Letzte Änderung an User binden
        
    db.commit()
    db.refresh(db_item)

    # WEBSOCKET BROADCAST - Jetzt inklusive Kategorie
    await manager.broadcast(db_item.list_id, {
        "event": "ITEM_UPDATED",
        "payload": {
            "list_id": db_item.list_id,
            "item": { "id": db_item.id, "name": db_item.name, "status": db_item.status, "quantity": db_item.quantity, "unit": db_item.unit, "category": db_item.category, "tags": db_item.tags }
        }
    })
    
    return db_item
    
@app.delete("/api/items/{item_id}")
async def delete_item(
    item_id: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # SCHUTZ
):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item nicht gefunden")
    
    list_id = db_item.list_id
    db.delete(db_item)
    db.commit()

    # WEBSOCKET BROADCAST
    await manager.broadcast(list_id, {
        "event": "ITEM_DELETED",
        "payload": {
            "list_id": list_id,
            "item_id": item_id
        }
    })
    
    return {"status": "ok", "message": "Item gelöscht"}