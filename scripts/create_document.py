"""
Helper script to create documents for RAG mode
Usage: python scripts/create_document.py <filename> <content>
"""
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Document
from app.services.rag_service import RAGService

def create_document(filename: str, content: str):
    """Create a document with chunking"""
    db: Session = SessionLocal()
    try:
        rag_service = RAGService()
        chunks = rag_service.chunk_document(content)
        
        document = Document(
            filename=filename,
            content=content,
            chunks=chunks,
            doc_metadata={"source": "manual_upload"}
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        print(f"Document created with ID: {document.id}")
        print(f"Filename: {filename}")
        print(f"Chunks: {len(chunks)}")
        return document.id
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_document.py <filename> <content>")
        sys.exit(1)
    
    filename = sys.argv[1]
    content = sys.argv[2]
    create_document(filename, content)

