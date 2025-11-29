"""
LLM Integration Service
Handles communication with external LLM providers
"""
from typing import List, Dict, Optional
from groq import Groq
import os


class LLMService:
    """Service for interacting with LLM APIs"""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        self.default_model = "llama-3.1-8b-instant"  # Free, fast model
        self.max_tokens = 2048
        self.max_context_tokens = 32768  # Model context limit
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """
        Generate response from LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to self.default_model)
            system_prompt: Optional system prompt
            max_tokens: Max tokens for response
            
        Returns:
            Dict with 'content', 'tokens_used', 'model_used'
        """
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        
        # Prepare messages
        chat_messages = []
        if system_prompt:
            chat_messages.append({
                "role": "system",
                "content": system_prompt
            })
        chat_messages.extend(messages)
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=chat_messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model_used": model
            }
        except Exception as e:
            raise Exception(f"LLM API error: {str(e)}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (4 chars ≈ 1 token)
        For production, use tiktoken or similar
        """
        return len(text) // 4
    
    def truncate_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        keep_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Truncate message history to fit within token limit
        Uses sliding window: keeps most recent messages
        """
        if not messages:
            return messages
        
        # Estimate tokens for each message
        message_tokens = []
        for msg in messages:
            tokens = self.estimate_tokens(msg.get("content", ""))
            message_tokens.append(tokens)
        
        total_tokens = sum(message_tokens)
        
        # If within limit, return as is
        if total_tokens <= max_tokens:
            return messages
        
        # Keep system message if present
        result = []
        if messages[0].get("role") == "system" and keep_system:
            result.append(messages[0])
            total_tokens = message_tokens[0]
            start_idx = 1
        else:
            start_idx = 0
        
        # Add messages from the end until we hit the limit
        for i in range(len(messages) - 1, start_idx - 1, -1):
            if total_tokens + message_tokens[i] <= max_tokens:
                result.insert(len(result) - (len(messages) - i), messages[i])
                total_tokens += message_tokens[i]
            else:
                break
        
        return result

