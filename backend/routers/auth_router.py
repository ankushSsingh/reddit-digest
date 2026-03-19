from fastapi import APIRouter, Depends, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import make_flow, get_google_userinfo, upsert_user, create_session_cookie, require_user
from ..models import User

router = APIRouter()


@router.get("/login")
async def login():
    flow = make_flow()
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    response = RedirectResponse(auth_url)
    # Store the PKCE code_verifier so we can pass it back during token exchange
    if getattr(flow, "code_verifier", None):
        response.set_cookie("cv", flow.code_verifier, httponly=True, max_age=600, samesite="lax")
    return response


@router.get("/callback")
async def callback(code: str, request: Request, db: Session = Depends(get_db)):
    flow = make_flow()
    code_verifier = request.cookies.get("cv")
    flow.fetch_token(code=code, code_verifier=code_verifier)
    userinfo = get_google_userinfo(flow.credentials.token)

    user = upsert_user(db, userinfo["id"], userinfo["email"], userinfo.get("name", ""))
    token = create_session_cookie(user.id)

    response = RedirectResponse(url="/dashboard.html", status_code=302)
    response.set_cookie("session", token, httponly=True, max_age=86400 * 7, samesite="lax")
    response.delete_cookie("cv")
    return response


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session")
    return {"ok": True}


@router.get("/me")
async def me(user: User = Depends(require_user)):
    return {"id": user.id, "email": user.email, "name": user.name}
