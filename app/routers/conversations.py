"""
Conversation API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.conversation_service import ConversationService
from app.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationUpdate,
    ConversationListResponse,
    MessageResponse,
    ErrorResponse
)

router = APIRouter()
conversation_service = ConversationService()


@router.post("/conversations", response_model=ConversationDetailResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new conversation with first message
    
    - **first_message**: The initial user message
    - **mode**: "open" for general chat or "rag" for document-grounded chat
    - **document_ids**: Optional list of document IDs (required for RAG mode)
    """
    try:
        # Get or create default user
        user = conversation_service.get_or_create_user(db)
        
        # Validate RAG mode
        if data.mode == "rag" and (not data.document_ids or len(data.document_ids) == 0):
            raise HTTPException(
                status_code=400,
                detail="document_ids required for RAG mode"
            )
        
        conversation = conversation_service.create_conversation(db, user.id, data)
        
        # Get messages
        messages = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                tokens_used=msg.tokens_used,
                model_used=msg.model_used,
                created_at=msg.created_at
            )
            for msg in conversation.messages
        ]
        
        # Get document IDs
        doc_ids = [link.document_id for link in conversation.document_links]
        
        return ConversationDetailResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            mode=conversation.mode,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(messages),
            messages=messages,
            document_ids=doc_ids if doc_ids else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all conversations with pagination
    
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    """
    try:
        user = conversation_service.get_or_create_user(db)
        conversations, total = conversation_service.list_conversations(
            db, user.id, page, page_size
        )
        
        conversation_responses = [
            ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                mode=conv.mode,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(conv.messages)
            )
            for conv in conversations
        ]
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get full conversation details including all messages
    
    - **conversation_id**: ID of the conversation
    """
    conversation = conversation_service.get_conversation(db, conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = [
        MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            tokens_used=msg.tokens_used,
            model_used=msg.model_used,
            created_at=msg.created_at
        )
        for msg in conversation.messages
    ]
    
    doc_ids = [link.document_id for link in conversation.document_links]
    
    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        mode=conversation.mode,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(messages),
        messages=messages,
        document_ids=doc_ids if doc_ids else None
    )


@router.put("/conversations/{conversation_id}", response_model=MessageResponse)
async def update_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """
    Add a new message to an existing conversation
    
    - **conversation_id**: ID of the conversation
    - **message**: New user message to add
    """
    try:
        message = conversation_service.add_message(db, conversation_id, data.message)
        
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            tokens_used=message.tokens_used,
            model_used=message.model_used,
            created_at=message.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages
    
    - **conversation_id**: ID of the conversation to delete
    """
    success = conversation_service.delete_conversation(db, conversation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return None

