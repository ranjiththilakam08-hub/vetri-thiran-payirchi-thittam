import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router


app = FastAPI(
    title="LegalEase API",
    description="AI-assisted legal document drafting API.",
    version="1.0.0",
)


origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    ).split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/", tags=["system"])
def root():
    return {
        "name": "LegalEase API",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }