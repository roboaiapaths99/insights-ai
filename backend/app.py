from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api import api_router
from db.init_db import init_db

app = FastAPI(title=settings.PROJECT_NAME)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create tables
init_db()

app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
