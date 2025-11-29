"""
Unit tests for conversation endpoints
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Set dummy API key for tests
os.environ["GROQ_API_KEY"] = "test_key"

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@patch('app.services.llm_service.Groq')
def test_create_conversation(mock_groq, client):
    """Test creating a new conversation"""
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello! I'm doing well, thank you!"
    mock_response.usage.total_tokens = 50
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq.return_value = mock_client
    
    response = client.post(
        "/api/v1/conversations",
        json={
            "first_message": "Hello, how are you?",
            "mode": "open"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["mode"] == "open"
    assert len(data["messages"]) >= 1  # At least user message


@patch('app.services.llm_service.Groq')
def test_list_conversations(mock_groq, client):
    """Test listing conversations"""
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage.total_tokens = 50
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq.return_value = mock_client
    
    # Create a conversation first
    client.post(
        "/api/v1/conversations",
        json={"first_message": "Test message", "mode": "open"}
    )
    
    # List conversations
    response = client.get("/api/v1/conversations")
    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert "total" in data
    assert len(data["conversations"]) > 0


@patch('app.services.llm_service.Groq')
def test_get_conversation(mock_groq, client):
    """Test getting a specific conversation"""
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage.total_tokens = 50
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq.return_value = mock_client
    
    # Create conversation
    create_response = client.post(
        "/api/v1/conversations",
        json={"first_message": "Test", "mode": "open"}
    )
    conversation_id = create_response.json()["id"]
    
    # Get conversation
    response = client.get(f"/api/v1/conversations/{conversation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation_id
    assert "messages" in data


@patch('app.services.llm_service.Groq')
def test_add_message_to_conversation(mock_groq, client):
    """Test adding a message to existing conversation"""
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage.total_tokens = 50
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq.return_value = mock_client
    
    # Create conversation
    create_response = client.post(
        "/api/v1/conversations",
        json={"first_message": "First message", "mode": "open"}
    )
    conversation_id = create_response.json()["id"]
    
    # Add message
    response = client.put(
        f"/api/v1/conversations/{conversation_id}",
        json={"message": "Follow-up question"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert data["content"] == "Follow-up question"


@patch('app.services.llm_service.Groq')
def test_delete_conversation(mock_groq, client):
    """Test deleting a conversation"""
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage.total_tokens = 50
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq.return_value = mock_client
    
    # Create conversation
    create_response = client.post(
        "/api/v1/conversations",
        json={"first_message": "Test", "mode": "open"}
    )
    conversation_id = create_response.json()["id"]
    
    # Delete conversation
    response = client.delete(f"/api/v1/conversations/{conversation_id}")
    assert response.status_code == 204
    
    # Verify deleted
    get_response = client.get(f"/api/v1/conversations/{conversation_id}")
    assert get_response.status_code == 404

