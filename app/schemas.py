"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(default="user", pattern="^(user|assistant)$")


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    tokens_used: int
    model_used: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    first_message: str = Field(..., min_length=1, max_length=10000)
    mode: str = Field(default="open", pattern="^(open|rag)$")
    document_ids: Optional[List[int]] = Field(default=None)


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    mode: str
    created_at: datetime
    updated_at: Optional[datetime]
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse]
    document_ids: Optional[List[int]] = None


class ConversationUpdate(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

