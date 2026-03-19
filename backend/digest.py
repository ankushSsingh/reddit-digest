import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .models import Digest
from .reddit import fetch_top_posts

CACHE_TTL_HOURS = 24


def get_or_generate_digest(user_id: int, subreddit: str, db: Session) -> dict:
    cutoff = datetime.utcnow() - timedelta(hours=CACHE_TTL_HOURS)
    cached = (
        db.query(Digest)
        .filter(Digest.user_id == user_id, Digest.subreddit == subreddit.lower())
        .filter(Digest.generated_at >= cutoff)
        .order_by(Digest.generated_at.desc())
        .first()
    )

    if cached:
        return {
            "subreddit": subreddit,
            "posts": json.loads(cached.content),
            "generated_at": cached.generated_at.isoformat(),
            "cached": True,
        }

    posts = fetch_top_posts(subreddit)
    now = datetime.utcnow()

    # Delete any stale cache entries for this user+subreddit
    db.query(Digest).filter(Digest.user_id == user_id, Digest.subreddit == subreddit.lower()).delete()

    entry = Digest(user_id=user_id, subreddit=subreddit.lower(), content=json.dumps(posts), generated_at=now)
    db.add(entry)
    db.commit()

    return {
        "subreddit": subreddit,
        "posts": posts,
        "generated_at": now.isoformat(),
        "cached": False,
    }


def delete_digest(user_id: int, subreddit: str, db: Session):
    db.query(Digest).filter(Digest.user_id == user_id, Digest.subreddit == subreddit.lower()).delete()
    db.commit()
