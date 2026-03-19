from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import require_user
from ..models import User
from ..digest import get_or_generate_digest, delete_digest
from ..email_sender import send_digest_email

router = APIRouter()


@router.get("/{subreddit}")
async def preview_digest(subreddit: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    try:
        return get_or_generate_digest(user.id, subreddit, db)
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch digest: {e}")


@router.post("/{subreddit}/email")
async def email_digest(subreddit: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    try:
        digest = get_or_generate_digest(user.id, subreddit, db)
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch digest: {e}")

    try:
        send_digest_email(user.email, subreddit, digest["posts"])
    except Exception as e:
        raise HTTPException(500, f"Failed to send email: {e}")

    return {"ok": True, "sent_to": user.email}


@router.delete("/{subreddit}")
async def clear_digest(subreddit: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    delete_digest(user.id, subreddit, db)
    return {"ok": True}
