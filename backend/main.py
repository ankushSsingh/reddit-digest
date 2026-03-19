from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .routers import auth_router, subreddits_router, digest_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Reddit Digest")

app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(subreddits_router.router, prefix="/api/subreddits", tags=["subreddits"])
app.include_router(digest_router.router, prefix="/api/digest", tags=["digest"])

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
