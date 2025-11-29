"""
BOT GPT - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import conversations, health

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BOT GPT API",
    description="Conversational AI Backend for BOT Consulting",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(conversations.router, prefix="/api/v1", tags=["Conversations"])


@app.get("/")
async def root():
    return {
        "message": "BOT GPT API",
        "version": "1.0.0",
        "docs": "/docs"
    }

