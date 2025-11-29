# BOT GPT - Conversational AI Backend

A production-grade conversational AI platform backend built with FastAPI, supporting both open chat and RAG (Retrieval-Augmented Generation) modes.

**Built for BOT Consulting - Associate AI Software Engineer Assessment**

## 🎯 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variable
export GROQ_API_KEY="your_api_key_here"  # Get free key at https://console.groq.com

# 3. Run server
uvicorn app.main:app --reload

# 4. Access API docs
# Open: http://localhost:8000/docs
```

See `QUICKSTART.md` for detailed setup instructions.

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Client/API    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│         FastAPI Layer               │
│  (REST API Endpoints)               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      Service Layer                  │
│  • ConversationService              │
│  • LLMService                       │
│  • RAGService                       │
└────────┬────────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────────────┐
│  SQLite│ │   Groq API        │
│  DB    │ │   (LLM Provider)  │
└────────┘ └──────────────────┘
```

### Tech Stack

- **Framework**: FastAPI (Python 3.11+)
  - Fast, modern, async support
  - Auto-generated API documentation
  - Type validation with Pydantic
  
- **Database**: SQLite (can be upgraded to PostgreSQL)
  - Simple setup for development
  - SQLAlchemy ORM for data modeling
  - Easy migration path to production DB

- **LLM Provider**: Groq API
  - Free tier available
  - Fast inference with Llama models
  - Low latency

- **Testing**: pytest
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## 📊 Data Model

### Entities

1. **User**
   - `id`, `username`, `email`, `created_at`

2. **Conversation**
   - `id`, `user_id`, `title`, `mode` (open/rag), `created_at`, `updated_at`

3. **Message**
   - `id`, `conversation_id`, `role` (user/assistant), `content`, `tokens_used`, `model_used`, `created_at`

4. **Document** (for RAG mode)
   - `id`, `filename`, `content`, `chunks`, `metadata`, `created_at`

5. **ConversationDocument** (link table)
   - Links conversations to documents for RAG mode

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### 1. Create Conversation
```http
POST /conversations
Content-Type: application/json

{
  "first_message": "Hello, how are you?",
  "mode": "open",  // or "rag"
  "document_ids": [1, 2]  // optional, required for RAG mode
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Hello, how are you?",
  "mode": "open",
  "created_at": "2024-01-01T12:00:00",
  "messages": [...],
  "message_count": 2
}
```

#### 2. List Conversations
```http
GET /conversations?page=1&page_size=20
```

**Response:**
```json
{
  "conversations": [...],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

#### 3. Get Conversation
```http
GET /conversations/{conversation_id}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "...",
  "mode": "open",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "...",
      "tokens_used": 10,
      "created_at": "..."
    },
    ...
  ]
}
```

#### 4. Add Message
```http
PUT /conversations/{conversation_id}
Content-Type: application/json

{
  "message": "What is the weather today?"
}
```

**Response:**
```json
{
  "id": 5,
  "conversation_id": 1,
  "role": "user",
  "content": "What is the weather today?",
  "tokens_used": 0,
  "created_at": "..."
}
```

#### 5. Delete Conversation
```http
DELETE /conversations/{conversation_id}
```

**Response:** `204 No Content`

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11+
- Groq API key (free at https://console.groq.com)

### Local Development

1. **Clone repository**
```bash
git clone <repo-url>
cd task
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set environment variables**

Create a `.env` file in the project root:
```bash
# Create .env file
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
echo "DATABASE_URL=sqlite:///./bot_gpt.db" >> .env
```

Or manually create `.env` with:
```
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./bot_gpt.db
```

Get your free Groq API key at: https://console.groq.com

5. **Run database migrations** (automatic on first run)
```bash
# Database tables are created automatically
```

6. **Start the server**
```bash
uvicorn app.main:app --reload
```

7. **Access API docs**
```
http://localhost:8000/docs
```

### Docker Setup

1. **Build and run**
```bash
docker-compose up --build
```

2. **Access API**
```
http://localhost:8000
```

## 🧪 Testing

Run tests:
```bash
pytest tests/ -v
```

## 🔄 LLM Context & Cost Management

### Context Construction
- Messages are formatted as `{role, content}` pairs
- System prompts added for RAG mode
- Conversation history maintained in chronological order

### Token Limit Handling
- **Sliding Window**: When history exceeds model limits, older messages are truncated
- Keeps most recent messages within token budget
- System prompts preserved when possible

### Cost Optimization Strategies
1. **Message Truncation**: Automatic truncation before LLM calls
2. **Token Tracking**: Track usage per message for monitoring
3. **Model Selection**: Use efficient models (Llama 3.1 8B Instant)
4. **Caching**: (Future) Cache common responses

## 🔍 RAG (Retrieval-Augmented Generation)

### Current Implementation
- **Document Storage**: Documents stored in database with content and chunks
- **Retrieval**: Simple keyword matching (simulated)
- **Context Injection**: Retrieved chunks added to system prompt

### Production RAG Flow (Designed)
1. **Document Ingestion**
   - Upload document → Chunk → Generate embeddings → Store in vector DB

2. **Query Time**
   - User query → Generate query embedding → Vector similarity search → Retrieve top-k chunks → Inject into LLM prompt

3. **Technologies** (for production)
   - Embeddings: OpenAI, Sentence Transformers
   - Vector DB: Pinecone, Weaviate, Chroma
   - Chunking: LangChain, custom strategies

## ⚠️ Error Handling

### Failure Points & Strategies

1. **LLM API Timeout**
   - Retry with exponential backoff
   - Fallback error message to user
   - Log error for monitoring

2. **Database Write Failure**
   - Transaction rollback
   - Return 500 error
   - Log for investigation

3. **Token Limit Breach**
   - Automatic message truncation
   - Warning in response metadata
   - Continue with truncated context

4. **Invalid Request**
   - Pydantic validation
   - Clear error messages
   - 400 status codes

## 📈 Scalability

### Current Bottlenecks (1M users)

1. **Database Layer**
   - SQLite not suitable for production scale
   - **Solution**: Migrate to PostgreSQL with connection pooling

2. **LLM API Calls**
   - Synchronous calls block requests
   - **Solution**: Async/await, request queuing, rate limiting

3. **Message History Loading**
   - Loading all messages for each request
   - **Solution**: Pagination, lazy loading, caching

### Scaling Strategies

1. **Horizontal Scaling**
   - Multiple FastAPI instances behind load balancer
   - Stateless API design supports this

2. **Database Sharding**
   - Shard by user_id or conversation_id
   - Read replicas for queries

3. **Caching**
   - Redis for frequently accessed conversations
   - Cache LLM responses for similar queries

4. **Message Queue**
   - Queue LLM requests for async processing
   - WebSocket for real-time updates

## 📝 Design Decisions

1. **SQLite for Development**
   - Simple setup, easy migration to PostgreSQL
   - SQLAlchemy abstracts database differences

2. **FastAPI Framework**
   - Modern async support
   - Built-in validation and docs
   - High performance

3. **Service Layer Pattern**
   - Separation of concerns
   - Easy testing and maintenance
   - Business logic isolated from API

4. **Message Truncation Strategy**
   - Sliding window keeps recent context
   - Better than summarization for cost/quality tradeoff

## 🔐 Security Considerations

- API key stored in environment variables
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy
- CORS configured (adjust for production)

## 📚 Additional Resources

- API Documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🛠️ Development

### Project Structure
```
task/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── database.py          # DB config
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/             # API routes
│   │   ├── conversations.py
│   │   └── health.py
│   └── services/            # Business logic
│       ├── conversation_service.py
│       ├── llm_service.py
│       └── rag_service.py
├── tests/
│   └── test_conversations.py
├── .github/workflows/
│   └── ci.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 📄 License

This project is part of a technical assessment for BOT Consulting.

