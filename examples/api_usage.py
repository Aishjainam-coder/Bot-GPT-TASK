"""
Example script demonstrating API usage
Run this after starting the server: uvicorn app.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def print_response(response, title="Response"):
    """Pretty print API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(json.dumps(response, indent=2))

# 1. Create a conversation (Open Chat Mode)
print("\n1. Creating a new conversation (Open Chat Mode)...")
response = requests.post(
    f"{BASE_URL}/conversations",
    json={
        "first_message": "Hello! Can you tell me about Python?",
        "mode": "open"
    }
)
conversation = response.json()
print_response(conversation, "Created Conversation")
conversation_id = conversation["id"]

# 2. Add a message to the conversation
print("\n2. Adding a follow-up message...")
response = requests.put(
    f"{BASE_URL}/conversations/{conversation_id}",
    json={
        "message": "What are the main features of Python?"
    }
)
message = response.json()
print_response(message, "New Message Added")

# 3. Get full conversation
print("\n3. Retrieving full conversation...")
response = requests.get(f"{BASE_URL}/conversations/{conversation_id}")
conversation = response.json()
print_response(conversation, "Full Conversation")
print(f"\nTotal messages: {len(conversation['messages'])}")

# 4. List all conversations
print("\n4. Listing all conversations...")
response = requests.get(f"{BASE_URL}/conversations?page=1&page_size=10")
conversations_list = response.json()
print_response(conversations_list, "Conversations List")
print(f"\nTotal conversations: {conversations_list['total']}")

# 5. Create RAG conversation (requires documents - this will fail without setup)
print("\n5. Attempting to create RAG conversation...")
print("Note: This requires documents to be created first using scripts/create_document.py")
response = requests.post(
    f"{BASE_URL}/conversations",
    json={
        "first_message": "What is in the document?",
        "mode": "rag",
        "document_ids": [1]  # This will fail if document doesn't exist
    }
)
if response.status_code == 201:
    print_response(response.json(), "RAG Conversation Created")
else:
    print(f"Expected error (document not found): {response.status_code}")
    print(response.json())

# 6. Delete a conversation
print("\n6. Deleting the first conversation...")
response = requests.delete(f"{BASE_URL}/conversations/{conversation_id}")
print(f"Delete status: {response.status_code} (204 = success)")

print("\n" + "="*50)
print("API Usage Examples Complete!")
print("="*50)

