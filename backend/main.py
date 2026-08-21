import os
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Dict
from datetime import timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models, schemas, auth
from database import engine, get_db
import json
from pywebpush import webpush, WebPushException

# Erstellt alle Tabellen in der Datenbank
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="KaufSync API", version="1.0.0")

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {"sub": "mailto:admin@kaufsync.com"}

def send_push_notification(subscription_info: dict, payload: dict):
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException as ex:
        print("I'm sorry, Dave, I'm afraid I can't do that: {}", repr(ex))
        # Mozilla returns additional information in the body of the response.
        if ex.response and ex.response.json():
            extra = ex.response.json()
            print("Remote service replied with a {}:{}, {}",
                  extra.code,
                  extra.errno,
                  extra.message
                  )

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
        # Speichert aktive Verbindungen pro User (user_id)
        self.user_active_connections: Dict[str, List[WebSocket]] = {}

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
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def connect_user(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.user_active_connections:
            self.user_active_connections[user_id] = []
        self.user_active_connections[user_id].append(websocket)

    def disconnect_user(self, websocket: WebSocket, user_id: str):
        if user_id in self.user_active_connections:
            self.user_active_connections[user_id].remove(websocket)

    async def broadcast_user(self, user_id: str, message: dict):
        if user_id in self.user_active_connections:
            for connection in self.user_active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

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


@app.websocket("/ws/user/{user_id}")
async def user_websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect_user(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_id)

# --- REST ENDPUNKTE ---
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "KaufSync Backend läuft!"}
    
# --- AUTHENTIFIZIERUNG ---

from fastapi import BackgroundTasks

@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Prüfen ob Email schon existiert
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-Mail bereits registriert")
        
    hashed_password = auth.get_password_hash(user_data.password)

    user_count = db.query(models.User).count()
    is_first_user = (user_count == 0)

    new_user = models.User(
        email=user_data.email, 
        password_hash=hashed_password, 
        display_name=user_data.display_name,
        is_admin=is_first_user,
        status="active" if is_first_user else "pending"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if new_user.status == "pending":
        admins = db.query(models.User).filter(
            models.User.is_admin == True,
            models.User.settings_push_admin_pending_users == True
        ).all()

        for admin in admins:
            # Create notification
            notification = models.Notification(
                user_id=admin.id,
                title="Neuer Nutzer wartet auf Freigabe",
                body=f"Der Nutzer {new_user.display_name} hat sich registriert und wartet auf Freigabe.",
                action_url="/admin"
            )
            db.add(notification)

            # Send push notification
            subscriptions = db.query(models.PushSubscription).filter(models.PushSubscription.user_id == admin.id).all()
            for sub in subscriptions:
                sub_info = {
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                }
                payload = {
                    "title": notification.title,
                    "body": notification.body,
                    "url": notification.action_url
                }
                background_tasks.add_task(send_push_notification, sub_info, payload)
        db.commit()

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
        "user": {"id": user.id, "name": user.display_name, "status": user.status}
    }
# --- ADMIN ENDPUNKTE ---
def get_admin_user(current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Keine Admin-Rechte")
    return current_user

@app.get("/api/push/public-key")
def get_push_public_key():
    return {"public_key": VAPID_PUBLIC_KEY}

@app.get("/api/admin/stats")
def get_admin_stats(db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    list_count = db.query(models.List).count()
    user_count = db.query(models.User).count()
    item_count = db.query(models.Item).count()

    # Optional: fetch user list for the admin view to display beneath stats
    users = db.query(models.User).all()

    return {
        "lists": list_count,
        "users": user_count,
        "items": item_count,
        "user_list": [{"id": u.id, "email": u.email, "display_name": u.display_name, "is_admin": u.is_admin, "status": u.status} for u in users]
    }

class UserRoleUpdate(BaseModel):
    is_admin: bool

@app.patch("/api/admin/users/{user_id}/role")
def change_user_role(user_id: str, payload: UserRoleUpdate, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Du kannst deine eigenen Rechte nicht entziehen.")
    user.is_admin = payload.is_admin
    db.commit()
    return {"status": "ok", "message": f"{user.display_name} ist nun {'Admin' if user.is_admin else 'kein Admin mehr'}."}

from pydantic import BaseModel

class UserStatusUpdate(BaseModel):
    status: str

@app.patch("/api/admin/users/{user_id}/status")
def change_user_status(user_id: str, payload: UserStatusUpdate, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    if payload.status not in ["pending", "active", "locked"]:
        raise HTTPException(status_code=400, detail="Ungültiger Status")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    if user.id == admin.id and payload.status != "active":
        raise HTTPException(status_code=400, detail="Du kannst dich nicht selbst sperren.")
    user.status = payload.status
    db.commit()
    return {"status": "ok", "message": f"Status von {user.display_name} geändert auf {payload.status}."}

@app.post("/api/admin/users/{user_id}/reset-password")
def admin_generate_reset_token(user_id: str, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    import secrets
    from datetime import datetime, timedelta

    # Invalide alte Tokens
    db.query(models.PasswordResetToken).filter(models.PasswordResetToken.user_id == user.id).update({"is_used": True})

    plain_token = secrets.token_urlsafe(32)

    token_entry = models.PasswordResetToken(
        user_id=user.id,
        token=auth.get_password_hash(plain_token),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(token_entry)
    db.commit()

    # Der Link enthält nun die user_id und den Token
    return {"status": "ok", "reset_link": f"/reset-password?user_id={user.id}&token={plain_token}"}

class ResetPasswordConfirm(BaseModel):
    user_id: str
    token: str
    new_password: str

@app.post("/api/auth/reset-password")
def reset_password(payload: ResetPasswordConfirm, db: Session = Depends(get_db)):
    from datetime import datetime
    tokens = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == payload.user_id,
        models.PasswordResetToken.is_used == False,
        models.PasswordResetToken.expires_at > datetime.utcnow()
    ).all()

    valid_token = None
    for t in tokens:
        if auth.verify_password(payload.token, t.token):
            valid_token = t
            break

    if not valid_token:
        raise HTTPException(status_code=400, detail="Ungültiger oder abgelaufener Token")

    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    user.password_hash = auth.get_password_hash(payload.new_password)
    valid_token.is_used = True
    db.commit()

    return {"status": "ok", "message": "Passwort erfolgreich zurückgesetzt"}

# --- USER ENDPUNKTE ---

class UserUpdate(BaseModel):
    display_name: str
    settings_push_async_events: bool | None = None
    settings_push_new_items: bool | None = None
    settings_push_admin_pending_users: bool | None = None

class PasswordUpdate(BaseModel):
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
    """Aktualisiert das Profil des Nutzers."""
    current_user.display_name = user_update.display_name
    if user_update.settings_push_async_events is not None:
        current_user.settings_push_async_events = user_update.settings_push_async_events
    if user_update.settings_push_new_items is not None:
        current_user.settings_push_new_items = user_update.settings_push_new_items
    if user_update.settings_push_admin_pending_users is not None:
        current_user.settings_push_admin_pending_users = user_update.settings_push_admin_pending_users
    db.commit()
    db.refresh(current_user)
    return current_user

@app.get("/api/notifications", response_model=list[schemas.NotificationResponse])
def get_notifications(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Notification).filter(models.Notification.user_id == current_user.id).order_by(models.Notification.created_at.desc()).all()

@app.patch("/api/notifications/{notification_id}/read")
def read_notification(notification_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id, models.Notification.user_id == current_user.id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return {"status": "ok"}

@app.post("/api/push/subscribe")
def subscribe_push(sub_data: schemas.PushSubscriptionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Check if subscription already exists for endpoint
    existing = db.query(models.PushSubscription).filter(
        models.PushSubscription.user_id == current_user.id,
        models.PushSubscription.endpoint == sub_data.endpoint
    ).first()
    if not existing:
        new_sub = models.PushSubscription(
            user_id=current_user.id,
            endpoint=sub_data.endpoint,
            p256dh=sub_data.p256dh,
            auth=sub_data.auth
        )
        db.add(new_sub)
        db.commit()
    else:
        existing.p256dh = sub_data.p256dh
        existing.auth = sub_data.auth
        db.commit()
    return {"status": "ok"}

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
async def create_list(
    list_data: schemas.ListCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user) # SCHUTZ
):
    # Check if a list with the same name already exists for the user
    existing_list = db.query(models.List).filter(
        models.List.name == list_data.name,
        ((models.List.created_by == current_user.id) | (models.List.members.any(id=current_user.id)))
    ).first()
    if existing_list:
        return existing_list

    new_list = models.List(
        name=list_data.name, 
        icon_name=list_data.icon_name,
        created_by=current_user.id # Liste an User binden
    )
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    await manager.broadcast_user(str(current_user.id), {
        "event": "LIST_UPDATED"
    })
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
async def delete_list(
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
            await manager.broadcast_user(str(current_user.id), {
                "event": "LIST_UPDATED"
            })
            return {"status": "ok", "message": "Liste verlassen"}
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
        
    db.delete(db_list)
    db.commit()

    await manager.broadcast_user(str(current_user.id), {
        "event": "LIST_UPDATED"
    })

    return {"status": "ok", "message": "Liste erfolgreich gelöscht"}
    
@app.post("/api/lists/join", response_model=schemas.ListResponse)
async def join_list(
    join_data: schemas.JoinListRequest, 
    background_tasks: BackgroundTasks,
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

    # Prüfen ob eine Liste mit demselben Namen bereits in den Listen des Users existiert
    existing_list = db.query(models.List).filter(
        models.List.name == db_list.name,
        ((models.List.created_by == current_user.id) | (models.List.members.any(id=current_user.id)))
    ).first()
    if existing_list:
        raise HTTPException(status_code=400, detail="Eine Liste mit diesem Namen existiert bereits in deinen Listen.")
        
    # User als Mitglied hinzufügen
    db_list.members.append(current_user)
    db.commit()
    db.refresh(db_list)

    # Push Notifications senden
    # Deduplicate members to prevent sending duplicate notifications to the creator
    members_list = db_list.members + ([db_list.creator] if db_list.creator else [])
    members = {member.id: member for member in members_list}.values()
    for member in members:
        if member.id != current_user.id:
            notif = models.Notification(
                user_id=member.id,
                title="Neues Mitglied",
                body=f"{current_user.display_name} ist der Liste '{db_list.name}' beigetreten.",
                action_url=f"/list/{db_list.id}"
            )
            db.add(notif)
            if member.settings_push_async_events:
                subs = db.query(models.PushSubscription).filter(models.PushSubscription.user_id == member.id).all()
                for sub in subs:
                    background_tasks.add_task(
                        send_push_notification,
                        {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                        {"title": notif.title, "body": notif.body, "url": notif.action_url}
                    )
    db.commit()

    await manager.broadcast_user(str(current_user.id), {
        "event": "LIST_UPDATED"
    })

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
async def respond_to_invitation(
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

    if action == "accept":
        await manager.broadcast_user(str(current_user.id), {
            "event": "LIST_UPDATED"
        })

    return {"status": "ok", "message": f"Einladung {'angenommen' if action == 'accept' else 'abgelehnt'}"}

@app.post("/api/lists/{list_id}/items", response_model=schemas.ItemResponse)
async def create_item(
    list_id: str, 
    item_data: schemas.ItemCreate, 
    background_tasks: BackgroundTasks,
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

    # LOG ACTIVITY
    log_entry = models.ActivityLog(
        list_id=list_id,
        user_id=current_user.id,
        action_type="added",
        item_name=new_item.name
    )
    db.add(log_entry)
    db.commit()

    # Push Notification für neue Items
    # Deduplicate members to prevent sending duplicate notifications to the creator
    members_list = db_list.members + ([db_list.creator] if db_list.creator else [])
    members = {member.id: member for member in members_list}.values()
    for member in members:
        if member.id != current_user.id:
            notif = models.Notification(
                user_id=member.id,
                title="Neuer Artikel",
                body=f"{current_user.display_name} hat {new_item.name} zu '{db_list.name}' hinzugefügt.",
                action_url=f"/list/{db_list.id}"
            )
            db.add(notif)
            if member.settings_push_new_items:
                subs = db.query(models.PushSubscription).filter(models.PushSubscription.user_id == member.id).all()
                for sub in subs:
                    background_tasks.add_task(
                        send_push_notification,
                        {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                        {"title": notif.title, "body": notif.body, "url": notif.action_url}
                    )
    db.commit()

    # WEBSOCKET BROADCAST - Jetzt inklusive Kategorie
    await manager.broadcast(list_id, {
        "event": "ITEM_UPDATED",
        "payload": {
            "list_id": list_id,
            "item": { "id": new_item.id, "name": new_item.name, "status": new_item.status, "quantity": new_item.quantity, "unit": new_item.unit, "category": new_item.category, "tags": new_item.tags }
        }
    })

    await manager.broadcast(list_id, {
        "event": "CHANGELOG_UPDATED",
        "payload": {}
    })

    return new_item

@app.post("/api/lists/{list_id}/start-shopping")
async def start_shopping(
    list_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Liste nicht gefunden")

    # LOG ACTIVITY
    log_entry = models.ActivityLog(
        list_id=list_id,
        user_id=current_user.id,
        action_type="started",
        item_name="Einkauf gestartet" # Placeholder
    )
    db.add(log_entry)
    db.commit()

    # Push Notification für Einkaufsstart an Listenmitglieder (nicht den der startet)
    # Deduplicate members to prevent sending duplicate notifications to the creator
    members_list = db_list.members + ([db_list.creator] if db_list.creator else [])
    members = {member.id: member for member in members_list}.values()
    for member in members:
        if member.id != current_user.id:
            notif = models.Notification(
                user_id=member.id,
                title="Einkauf gestartet",
                body=f"{current_user.display_name} hat den Einkauf für '{db_list.name}' gestartet.",
                action_url=f"/list/{db_list.id}"
            )
            db.add(notif)
            if member.settings_push_async_events:
                subs = db.query(models.PushSubscription).filter(models.PushSubscription.user_id == member.id).all()
                for sub in subs:
                    background_tasks.add_task(
                        send_push_notification,
                        {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                        {"title": notif.title, "body": notif.body, "url": notif.action_url}
                    )
    db.commit()
    return {"status": "ok"}

@app.get("/api/lists/{list_id}/changelog", response_model=List[schemas.ActivityLogResponse])
async def get_list_changelog(
    list_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify user has access to list
    db_list = db.query(models.List).filter(models.List.id == list_id).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="Liste nicht gefunden")

    # Check if user is member or creator
    is_member = any(member.id == current_user.id for member in db_list.members)
    if db_list.created_by != current_user.id and not is_member:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diese Liste")

    logs = db.query(models.ActivityLog).filter(
        models.ActivityLog.list_id == list_id
    ).order_by(
        models.ActivityLog.created_at.desc()
    ).limit(50).all()

    # Add user_name
    for log in logs:
        user = db.query(models.User).filter(models.User.id == log.user_id).first()
        if user:
            log.user_name = user.display_name

    return logs


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
    
    if item_data.name is not None: db_item.name = item_data.name
    if item_data.unit is not None: db_item.unit = item_data.unit
    old_status = db_item.status
    if item_data.status is not None: db_item.status = item_data.status
    if item_data.quantity is not None: db_item.quantity = item_data.quantity
    if item_data.note is not None: db_item.note = item_data.note
    if hasattr(item_data, 'category') and item_data.category is not None: db_item.category = item_data.category
    if hasattr(item_data, 'tags') and item_data.tags is not None: db_item.tags = item_data.tags
    
    db_item.last_modified_by = current_user.id # Letzte Änderung an User binden
        
    db.commit()
    db.refresh(db_item)

    # LOG ACTIVITY (if status changed)
    if item_data.status is not None and old_status != item_data.status:
        action = "completed" if item_data.status == "completed" else "reactivated"
        log_entry = models.ActivityLog(
            list_id=db_item.list_id,
            user_id=current_user.id,
            action_type=action,
            item_name=db_item.name
        )
        db.add(log_entry)
        db.commit()

        await manager.broadcast(db_item.list_id, {
            "event": "CHANGELOG_UPDATED",
            "payload": {}
        })

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
    item_name = db_item.name
    db.delete(db_item)
    db.commit()

    # LOG ACTIVITY
    log_entry = models.ActivityLog(
        list_id=list_id,
        user_id=current_user.id,
        action_type="deleted",
        item_name=item_name
    )
    db.add(log_entry)
    db.commit()

    # WEBSOCKET BROADCAST
    await manager.broadcast(list_id, {
        "event": "ITEM_DELETED",
        "payload": {
            "list_id": list_id,
            "item_id": item_id
        }
    })
    
    await manager.broadcast(list_id, {
        "event": "CHANGELOG_UPDATED",
        "payload": {}
    })

    return {"status": "ok", "message": "Item gelöscht"}

import pathlib

# --- STATIC FILES & SPA FALLBACK ---
@app.get("/{full_path:path}")
async def serve_static(full_path: str):
    """
    Catch-all Route für das Ausliefern der Vue.js SPA und statischer Dateien.
    Alle Anfragen, die nicht von der API (/api/...) oder WebSockets (/ws/...)
    gefangen werden, landen hier.
    """
    # Verhindere, dass API oder WS Routen als statische Dateien oder index.html beantwortet werden
    if full_path.startswith("api/") or full_path.startswith("ws/"):
        raise HTTPException(status_code=404, detail="Not found")

    static_dir = pathlib.Path("static").resolve()
    # Sichere Pfad-Auflösung gegen Path-Traversal
    # .resolve() entfernt /../ und macht den Pfad absolut.
    file_path = (static_dir / full_path).resolve()

    # Sicherstellen, dass die Datei auch WIRKLICH im static_dir liegt
    try:
        file_path.relative_to(static_dir)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")

    # Prüfen, ob die Datei existiert (z.B. /assets/main.js) und kein Verzeichnis ist
    if full_path and file_path.is_file():
        return FileResponse(file_path)

    # Ansonsten immer die index.html ausliefern (Vue Router History-Modus Fallback)
    index_path = static_dir / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Static files not found")