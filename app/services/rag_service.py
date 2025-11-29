"""
RAG (Retrieval-Augmented Generation) Service
Handles document retrieval and context construction
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models import Document, ConversationDocument, Conversation


class RAGService:
    """Service for RAG operations"""
    
    def __init__(self):
        # In production, this would use embeddings and vector DB
        # For now, we simulate with simple text matching
        pass
    
    def retrieve_relevant_chunks(
        self,
        db: Session,
        conversation_id: int,
        user_query: str,
        top_k: int = 3
    ) -> List[str]:
        """
        Retrieve relevant document chunks for a user query
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            user_query: User's query
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunk texts
        """
        # Get documents linked to this conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation or conversation.mode != "rag":
            return []
        
        # Get linked documents
        doc_links = db.query(ConversationDocument).filter(
            ConversationDocument.conversation_id == conversation_id
        ).all()
        
        if not doc_links:
            return []
        
        document_ids = [link.document_id for link in doc_links]
        documents = db.query(Document).filter(
            Document.id.in_(document_ids)
        ).all()
        
        # Simulate retrieval: simple keyword matching
        # In production, use embeddings + vector similarity search
        relevant_chunks = []
        query_lower = user_query.lower()
        query_words = set(query_lower.split())
        
        for doc in documents:
            if doc.chunks:
                # If chunks are stored, search through them
                for chunk in doc.chunks:
                    chunk_text = chunk.get("text", "").lower()
                    chunk_words = set(chunk_text.split())
                    # Simple relevance: count matching words
                    matches = len(query_words.intersection(chunk_words))
                    if matches > 0:
                        relevant_chunks.append({
                            "text": chunk.get("text", ""),
                            "score": matches,
                            "source": doc.filename
                        })
            elif doc.content:
                # If no chunks, use full content (simplified)
                content_lower = doc.content.lower()
                matches = len(query_words.intersection(set(content_lower.split())))
                if matches > 0:
                    # Split into sentences as chunks
                    sentences = doc.content.split('.')
                    for sent in sentences[:top_k]:
                        if any(word in sent.lower() for word in query_words):
                            relevant_chunks.append({
                                "text": sent.strip(),
                                "score": matches,
                                "source": doc.filename
                            })
        
        # Sort by score and return top_k
        relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
        return [chunk["text"] for chunk in relevant_chunks[:top_k]]
    
    def construct_rag_context(
        self,
        db: Session,
        conversation_id: int,
        user_query: str
    ) -> str:
        """
        Construct RAG context string from retrieved chunks
        
        Returns:
            Formatted context string to include in LLM prompt
        """
        chunks = self.retrieve_relevant_chunks(db, conversation_id, user_query)
        
        if not chunks:
            return ""
        
        context = "Relevant context from documents:\n\n"
        for i, chunk in enumerate(chunks, 1):
            context += f"[{i}] {chunk}\n\n"
        
        return context
    
    def chunk_document(self, content: str, chunk_size: int = 500) -> List[Dict]:
        """
        Simple document chunking (sentence-based)
        In production, use more sophisticated chunking strategies
        """
        sentences = content.split('.')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({"text": current_chunk.strip()})
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append({"text": current_chunk.strip()})
        
        return chunks

