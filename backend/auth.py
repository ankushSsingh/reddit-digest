from fastapi import Request, HTTPException, Depends
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session
import requests as req

from .config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, APP_SECRET_KEY
from .database import get_db
from .models import User

_serializer = URLSafeTimedSerializer(APP_SECRET_KEY)

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def make_flow() -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )


def create_session_cookie(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def read_session_cookie(token: str) -> int | None:
    try:
        data = _serializer.loads(token, max_age=86400 * 7)
        return data["user_id"]
    except (BadSignature, SignatureExpired, KeyError):
        return None


def get_google_userinfo(access_token: str) -> dict:
    resp = req.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def upsert_user(db: Session, google_id: str, email: str, name: str) -> User:
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        user.email = email
        user.name = name
    else:
        user = User(google_id=google_id, email=email, name=name)
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = read_session_cookie(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
