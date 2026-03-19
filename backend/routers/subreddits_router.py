from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..auth import require_user
from ..models import User, Subscription
from ..reddit import validate_subreddit
from ..digest import delete_digest

router = APIRouter()


class AddSubredditBody(BaseModel):
    subreddit: str


@router.get("")
async def list_subreddits(user: User = Depends(require_user), db: Session = Depends(get_db)):
    return [
        {"subreddit": s.subreddit, "added_at": s.added_at.isoformat()}
        for s in user.subscriptions
    ]


@router.post("")
async def add_subreddit(body: AddSubredditBody, user: User = Depends(require_user), db: Session = Depends(get_db)):
    name = body.subreddit.strip().lower()
    if not name:
        raise HTTPException(400, "Subreddit name is required")

    existing = db.query(Subscription).filter_by(user_id=user.id, subreddit=name).first()
    if existing:
        raise HTTPException(400, "Subreddit already added")

    if not validate_subreddit(name):
        raise HTTPException(404, f"r/{name} not found on Reddit")

    sub = Subscription(user_id=user.id, subreddit=name)
    db.add(sub)
    db.commit()
    return {"subreddit": name, "added_at": sub.added_at.isoformat()}


@router.delete("/{subreddit}")
async def remove_subreddit(subreddit: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    name = subreddit.lower()
    sub = db.query(Subscription).filter_by(user_id=user.id, subreddit=name).first()
    if not sub:
        raise HTTPException(404, "Subreddit not in your list")
    db.delete(sub)
    delete_digest(user.id, name, db)
    db.commit()
    return {"ok": True}
