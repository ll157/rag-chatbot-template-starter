from fastapi import FastAPI

from app.config import settings
from app.routers import chat, documents, upload

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="A minimal FastAPI starter for building RAG chatbots.",
)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.app_env}


app.include_router(upload.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
