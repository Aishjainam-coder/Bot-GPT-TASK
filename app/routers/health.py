"""
Health check endpoint
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "BOT GPT API"
    }

