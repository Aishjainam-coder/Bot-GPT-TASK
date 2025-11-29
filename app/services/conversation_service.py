"""
Conversation Service
Handles conversation logic and message management
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import User, Conversation, Message, Document, ConversationDocument
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.schemas import MessageCreate, ConversationCreate


class ConversationService:
    """Service for managing conversations"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.rag_service = RAGService()
    
    def get_or_create_user(self, db: Session, username: str = "default") -> User:
        """Get or create a default user"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    def create_conversation(
        self,
        db: Session,
        user_id: int,
        data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation with first message"""
        # Create conversation
        conversation = Conversation(
            user_id=user_id,
            mode=data.mode,
            title=data.first_message[:50] + "..." if len(data.first_message) > 50 else data.first_message
        )
        db.add(conversation)
        db.flush()
        
        # Link documents if RAG mode
        if data.mode == "rag" and data.document_ids:
            for doc_id in data.document_ids:
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    link = ConversationDocument(
                        conversation_id=conversation.id,
                        document_id=doc_id
                    )
                    db.add(link)
        
        # Create user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=data.first_message
        )
        db.add(user_message)
        db.flush()
        
        # Generate assistant response
        assistant_response = self._generate_response(
            db, conversation.id, data.first_message, data.mode
        )
        
        db.commit()
        db.refresh(conversation)
        return conversation
    
    def add_message(
        self,
        db: Session,
        conversation_id: int,
        content: str
    ) -> Message:
        """Add a new message to existing conversation"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError("Conversation not found")
        
        # Create user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=content
        )
        db.add(user_message)
        db.flush()
        
        # Generate assistant response
        assistant_response = self._generate_response(
            db, conversation_id, content, conversation.mode
        )
        
        db.commit()
        db.refresh(user_message)
        return user_message
    
    def _generate_response(
        self,
        db: Session,
        conversation_id: int,
        user_message: str,
        mode: str
    ) -> Message:
        """Generate assistant response using LLM"""
        # Get conversation history
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        # Prepare message history for LLM (exclude current user message as it's added separately)
        message_history = []
        for msg in messages:
            message_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # RAG mode: add retrieved context
        system_prompt = None
        if mode == "rag":
            context = self.rag_service.construct_rag_context(
                db, conversation_id, user_message
            )
            if context:
                system_prompt = (
                    "You are a helpful assistant that answers questions based on "
                    "the provided context. Use only the information from the context "
                    "to answer. If the context doesn't contain the answer, say so.\n\n"
                    f"{context}"
                )
        
        # Add current user message
        message_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Truncate if needed (keep last N messages within token limit)
        max_context = self.llm_service.max_context_tokens - self.llm_service.max_tokens
        message_history = self.llm_service.truncate_messages(
            message_history,
            max_context
        )
        
        # Call LLM
        try:
            response = self.llm_service.generate_response(
                messages=message_history,
                system_prompt=system_prompt
            )
        except Exception as e:
            # Fallback response on error
            response = {
                "content": f"I apologize, but I encountered an error: {str(e)}",
                "tokens_used": 0,
                "model_used": None
            }
        
        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response["content"],
            tokens_used=response.get("tokens_used", 0),
            model_used=response.get("model_used")
        )
        db.add(assistant_message)
        return assistant_message
    
    def get_conversation(self, db: Session, conversation_id: int) -> Optional[Conversation]:
        """Get conversation by ID"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def list_conversations(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Conversation], int]:
        """List conversations for a user with pagination"""
        offset = (page - 1) * page_size
        
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).offset(offset).limit(page_size).all()
        
        total = db.query(func.count(Conversation.id)).filter(
            Conversation.user_id == user_id
        ).scalar()
        
        return conversations, total
    
    def delete_conversation(self, db: Session, conversation_id: int) -> bool:
        """Delete a conversation"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return False
        
        db.delete(conversation)
        db.commit()
        return True

