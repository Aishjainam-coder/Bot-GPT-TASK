# BOT GPT - System Design Document

## 1. Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                           │
│              (Postman, cURL, Frontend Apps)                   │
└────────────────────────────┬──────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│                    FastAPI Application                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Conversations│  │   Health     │  │  Documents   │      │
│  │   Router     │  │   Router     │  │   Router     │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ Conversation     │  │   LLM Service    │                 │
│  │   Service        │  │                  │                 │
│  └────────┬─────────┘  └────────┬─────────┘                 │
│           │                     │                           │
│           └──────────┬───────────┘                           │
│                      │                                       │
│           ┌──────────▼──────────┐                           │
│           │   RAG Service       │                           │
│           │  (Retrieval Logic)  │                           │
│           └─────────────────────┘                           │
└────────────┬─────────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│ SQLite  │    │  Groq API    │
│   DB    │    │  (LLM)       │
└─────────┘    └──────────────┘
```

### Component Responsibilities

1. **API Layer (FastAPI)**
   - Request/response handling
   - Input validation (Pydantic)
   - Authentication/authorization (future)
   - Error handling

2. **Service Layer**
   - Business logic
   - Conversation management
   - LLM integration
   - RAG retrieval

3. **Data Layer**
   - Persistence (SQLAlchemy)
   - Data modeling
   - Query optimization

4. **External Services**
   - LLM API (Groq)
   - Future: Vector DB, Embedding service

## 2. Tech Stack Justification

### FastAPI (Python)
**Why:**
- **Performance**: Async/await support, comparable to Node.js
- **Developer Experience**: Auto-generated OpenAPI docs, type hints
- **Modern**: Built on Pydantic and Starlette
- **LLM Ecosystem**: Python has best LLM library support

**Alternatives Considered:**
- Node.js/Express: Good but Python better for AI/ML
- Django: Too heavy for API-only service
- Flask: Lacks async support, less modern

### SQLite → PostgreSQL
**Why SQLite for MVP:**
- Zero configuration
- File-based, easy to backup
- Sufficient for development/testing
- SQLAlchemy makes migration easy

**Why PostgreSQL for Production:**
- ACID compliance
- Concurrent connections
- Advanced indexing
- JSON support for flexible schemas

### Groq API
**Why:**
- **Free tier**: No cost for development
- **Fast**: Hardware acceleration
- **Llama models**: Open-source, capable
- **Simple**: REST API, easy integration

**Alternatives:**
- OpenAI: Expensive, rate limits
- Anthropic Claude: Expensive
- Local Ollama: Requires GPU, setup complexity

## 3. Data & Storage Design

### Database Schema

```sql
-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(255),
    mode VARCHAR(50) DEFAULT 'open',  -- 'open' or 'rag'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Messages
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    model_used VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Documents (for RAG)
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    content TEXT,
    chunks JSON,  -- Pre-processed chunks
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation-Document Links
CREATE TABLE conversation_documents (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

### Data Storage Strategy

**Conversation History:**
- Stored as individual messages with ordering
- `created_at` timestamp ensures chronological order
- Foreign key maintains referential integrity

**Message Ordering:**
- SQLAlchemy `order_by` on `created_at`
- Index on `(conversation_id, created_at)` for fast queries

**Token Tracking:**
- Stored per message for cost analysis
- Enables usage monitoring and budgeting

**Document Storage:**
- Full content in `content` field
- Pre-processed chunks in JSON `chunks` field
- Metadata for filtering/searching

## 4. REST API Design

### Endpoint Specifications

#### Base URL
```
http://localhost:8000/api/v1
```

#### 1. Create Conversation
```http
POST /conversations
Content-Type: application/json

Request Body:
{
  "first_message": "Hello, how are you?",
  "mode": "open",  // or "rag"
  "document_ids": [1, 2]  // optional, required for RAG
}

Response: 201 Created
{
  "id": 1,
  "user_id": 1,
  "title": "Hello, how are you?",
  "mode": "open",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": null,
  "message_count": 2,
  "messages": [...],
  "document_ids": null
}
```

**Design Decisions:**
- POST for creation (idempotent with unique IDs)
- Returns full conversation with messages
- Auto-generates title from first message

#### 2. List Conversations
```http
GET /conversations?page=1&page_size=20

Response: 200 OK
{
  "conversations": [...],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

**Design Decisions:**
- Pagination for scalability
- Default page_size=20, max=100
- Ordered by `updated_at DESC` (most recent first)

#### 3. Get Conversation
```http
GET /conversations/{conversation_id}

Response: 200 OK
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
      "model_used": "llama-3.1-8b-instant",
      "created_at": "..."
    },
    ...
  ]
}
```

**Design Decisions:**
- Returns full message history
- Includes metadata (tokens, model)

#### 4. Add Message
```http
PUT /conversations/{conversation_id}
Content-Type: application/json

Request Body:
{
  "message": "What is the weather?"
}

Response: 200 OK
{
  "id": 5,
  "conversation_id": 1,
  "role": "user",
  "content": "What is the weather?",
  "tokens_used": 0,
  "model_used": null,
  "created_at": "..."
}
```

**Design Decisions:**
- PUT for updating (adding to) conversation
- Returns only the new user message
- Assistant response generated automatically

#### 5. Delete Conversation
```http
DELETE /conversations/{conversation_id}

Response: 204 No Content
```

**Design Decisions:**
- Cascade delete messages (database constraint)
- Returns 204 (no content) on success

### Error Handling

| Status Code | Scenario |
|------------|----------|
| 200 | Success |
| 201 | Created |
| 204 | Deleted (no content) |
| 400 | Bad request (validation error) |
| 404 | Resource not found |
| 500 | Internal server error |

**Error Response Format:**
```json
{
  "error": "Conversation not found",
  "detail": "No conversation with ID 999 exists"
}
```

## 5. LLM Context & Cost Management

### Context Construction Flow

```
User Message
    │
    ▼
Get Conversation History
    │
    ▼
[If RAG Mode] Retrieve Relevant Chunks
    │
    ▼
Format Messages:
  - System Prompt (if RAG)
  - History Messages
  - Current User Message
    │
    ▼
Check Token Count
    │
    ▼
[If Exceeds Limit] Truncate (Sliding Window)
    │
    ▼
Call LLM API
    │
    ▼
Store Response + Tokens
```

### Token Limit Handling

**Problem:** LLM models have context limits (e.g., 32K tokens)

**Solution: Sliding Window**
1. Estimate tokens for each message
2. If total exceeds limit:
   - Keep system prompt (if present)
   - Keep most recent messages
   - Discard oldest messages

**Implementation:**
```python
def truncate_messages(messages, max_tokens):
    # Keep system message
    # Add messages from end until limit reached
    return truncated_messages
```

### Cost Optimization Strategies

1. **Message Truncation**
   - Prevents unnecessary token usage
   - Keeps context relevant (recent messages)

2. **Token Tracking**
   - Monitor usage per conversation
   - Enable budgeting and alerts

3. **Model Selection**
   - Use efficient models (Llama 3.1 8B)
   - Balance cost vs. quality

4. **Caching** (Future)
   - Cache common responses
   - Reduce redundant API calls

5. **Summarization** (Future)
   - Summarize old messages instead of truncating
   - Preserve more context

## 6. RAG (Retrieval-Augmented Generation) Design

### Current Implementation (Simulated)

**Flow:**
1. User starts RAG conversation with document IDs
2. Documents linked to conversation
3. On each message:
   - Extract keywords from user query
   - Match against document chunks (simple keyword matching)
   - Retrieve top-k chunks
   - Inject into system prompt

**Limitations:**
- No embeddings
- Simple keyword matching
- No vector similarity

### Production RAG Architecture (Designed)

```
Document Upload
    │
    ▼
Chunking (500-1000 chars)
    │
    ▼
Generate Embeddings
    │
    ▼
Store in Vector DB
    │
    ▼
[Query Time]
User Message
    │
    ▼
Generate Query Embedding
    │
    ▼
Vector Similarity Search
    │
    ▼
Retrieve Top-K Chunks
    │
    ▼
Inject into LLM Prompt
```

### Technologies for Production

**Embeddings:**
- OpenAI `text-embedding-ada-002`
- Sentence Transformers (free)
- Cohere Embeddings

**Vector Database:**
- Pinecone (managed)
- Weaviate (self-hosted)
- Chroma (lightweight)
- PostgreSQL with pgvector

**Chunking Strategy:**
- Sentence-based (current)
- Semantic chunking (better)
- Overlapping windows (preserve context)

## 7. Error Handling & Scalability

### Failure Points & Mitigation

| Failure Point | Impact | Mitigation |
|--------------|--------|------------|
| LLM API Timeout | User sees error | Retry with backoff, fallback message |
| LLM API Rate Limit | Request rejected | Queue requests, rate limiting |
| Database Write Failure | Data loss | Transaction rollback, retry |
| Token Limit Exceeded | Context truncated | Automatic truncation, warning |
| Invalid Request | Bad data | Pydantic validation, clear errors |

### Retry Strategy

```python
# Exponential backoff for LLM calls
max_retries = 3
for attempt in range(max_retries):
    try:
        response = llm_api.call(...)
        break
    except TimeoutError:
        wait = 2 ** attempt
        sleep(wait)
```

### Logging & Monitoring

**Log Levels:**
- ERROR: API failures, DB errors
- WARNING: Token limits, rate limits
- INFO: Request/response, token usage
- DEBUG: Detailed flow

**Metrics to Track:**
- Request latency
- Token usage per conversation
- LLM API errors
- Database query time

### Scalability Analysis

**Bottleneck at 1M Users:**

1. **Database Layer** (Primary)
   - SQLite: Single file, no concurrency
   - **Solution**: PostgreSQL with connection pooling

2. **LLM API Calls** (Secondary)
   - Synchronous blocking
   - **Solution**: Async/await, request queuing

3. **Message History Loading** (Tertiary)
   - Loading all messages per request
   - **Solution**: Pagination, lazy loading, caching

### Scaling Strategies

**Horizontal Scaling:**
- Multiple FastAPI instances
- Load balancer (nginx, AWS ALB)
- Stateless design (no session storage)

**Database Scaling:**
- Read replicas for queries
- Sharding by user_id
- Connection pooling (PgBouncer)

**Caching:**
- Redis for hot conversations
- Cache LLM responses (similarity-based)
- Reduce database load

**Message Queue:**
- RabbitMQ/Kafka for LLM requests
- Async processing
- WebSocket for real-time updates

## 8. Deployment & DevOps

### Docker Setup

**Dockerfile:**
- Multi-stage build (optional)
- Python 3.11 slim base
- Minimal dependencies
- Health check endpoint

**docker-compose.yml:**
- Service definition
- Environment variables
- Volume mounts for DB

### CI/CD Pipeline

**GitHub Actions:**
1. **Test Job**
   - Install dependencies
   - Run pytest
   - Lint with flake8

2. **Build Job**
   - Build Docker image
   - Tag with version

**Future Enhancements:**
- Deploy to staging
- Integration tests
- Security scanning

### Environment Configuration

**Development:**
- SQLite database
- Local file storage
- Debug logging

**Production:**
- PostgreSQL
- S3/cloud storage
- Structured logging (JSON)
- Monitoring (Prometheus, Grafana)

## 9. Security Considerations

1. **API Keys**
   - Stored in environment variables
   - Never committed to git
   - Rotate regularly

2. **Input Validation**
   - Pydantic schemas
   - SQL injection protection (SQLAlchemy)
   - XSS prevention

3. **Authentication** (Future)
   - JWT tokens
   - OAuth2
   - API key per user

4. **Rate Limiting** (Future)
   - Per-user limits
   - Per-IP limits
   - Prevent abuse

## 10. Future Enhancements

1. **Full RAG Implementation**
   - Embeddings + Vector DB
   - Semantic search
   - Multi-document support

2. **Streaming Responses**
   - Server-Sent Events (SSE)
   - Real-time token streaming

3. **Multi-LLM Support**
   - Provider abstraction
   - Fallback chains
   - Cost optimization

4. **Advanced Context Management**
   - Message summarization
   - Context compression
   - Smart truncation

5. **Analytics Dashboard**
   - Token usage per user
   - Cost tracking
   - Conversation analytics

## Conclusion

This design provides a solid foundation for a conversational AI backend with:
- Clean architecture and separation of concerns
- Scalable data model
- Cost-aware LLM integration
- RAG-ready design
- Production-ready patterns

The implementation prioritizes clarity, maintainability, and extensibility while meeting all core requirements.

