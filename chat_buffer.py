from typing import List, Dict, Optional
import tiktoken
from models import Message
import logging

logger = logging.getLogger(__name__)

class ChatBuffer:
    def __init__(self, max_tokens: int = 64000):
        self.max_tokens = max_tokens
        self.messages: List[Dict] = []
        self.encoding = tiktoken.get_encoding("cl100k_base")  # Using OpenAI's encoding for token counting
        logger.debug(f"Initialized new ChatBuffer with max_tokens={max_tokens}")
        
    def add_message(self, role: str, content: str) -> bool:
        """
        Add a message to the buffer and check if it exceeds the token limit.
        Returns True if the message was added successfully, False if it would exceed the limit.
        """
        # Count tokens for the new message
        new_tokens = len(self.encoding.encode(content))
        logger.debug(f"Adding message - Role: {role}, Tokens: {new_tokens}")
        
        # Count current tokens
        current_tokens = self.get_token_count()
        logger.debug(f"Current token count: {current_tokens}")
        
        # Check if adding the new message would exceed the limit
        if current_tokens + new_tokens > self.max_tokens:
            logger.warning(f"Message would exceed token limit. Current: {current_tokens}, New: {new_tokens}, Max: {self.max_tokens}")
            return False
            
        # Add the message to the buffer
        self.messages.append({
            'role': role,
            'content': content
        })
        logger.debug(f"Message added successfully. New total messages: {len(self.messages)}")
        return True
        
    def get_messages(self) -> List[Dict]:
        """Get all messages in the buffer."""
        logger.debug(f"Retrieving {len(self.messages)} messages from buffer")
        return self.messages.copy()  # Return a copy to prevent external modification
        
    def clear(self):
        """Clear the buffer."""
        logger.info(f"Clearing buffer with {len(self.messages)} messages")
        self.messages = []
        
    def get_token_count(self) -> int:
        """Get the current token count of all messages in the buffer."""
        total_tokens = 0
        for msg in self.messages:
            msg_tokens = len(self.encoding.encode(msg['content']))
            total_tokens += msg_tokens
            logger.debug(f"Message tokens - Role: {msg['role']}, Tokens: {msg_tokens}")
        logger.debug(f"Total token count: {total_tokens}")
        return total_tokens
        
    def load_from_db_messages(self, messages: List[Message]) -> bool:
        """
        Load messages from database into the buffer.
        Returns True if all messages were loaded successfully, False if it would exceed the limit.
        """
        logger.info(f"Loading {len(messages)} messages from database")
        # Clear current buffer
        self.clear()
        
        # Try to add each message
        for msg in messages:
            if not self.add_message(msg.role, msg.content):
                logger.warning(f"Failed to load all messages - buffer would exceed token limit")
                return False
        logger.info("Successfully loaded all messages from database")
        return True

    def format_for_gemma(self) -> str:
        """Format messages for Gemma model."""
        logger.debug("Formatting messages for Gemma model")
        conversation = []
        for msg in self.messages:
            role = msg['role']
            content = msg['content']
            if role == 'user':
                conversation.append(f"<start_of_turn>user\n{content}<end_of_turn>")
            else:
                conversation.append(f"<start_of_turn>model\n{content}<end_of_turn>")
        conversation.append("<start_of_turn>model\n")
        formatted = "\n".join(conversation)
        logger.debug(f"Formatted conversation length: {len(formatted)} characters")
        return formatted

    def format_for_gemma3(self) -> str:
        """Format messages for Gemma 3 model."""
        logger.debug("Formatting messages for Gemma 3 model")
        conversation = []
        for msg in self.messages:
            role = msg['role']
            content = msg['content']
            if role == 'user':
                conversation.append(f"<|user|>\n{content}<|end|>")
            else:
                conversation.append(f"<|assistant|>\n{content}<|end|>")
        conversation.append("<|assistant|>")
        formatted = "\n".join(conversation)
        logger.debug(f"Formatted conversation length: {len(formatted)} characters")
        return formatted

    def format_for_phi(self) -> str:
        """Format messages for Phi model."""
        logger.debug("Formatting messages for Phi model")
        conversation = []
        for msg in self.messages:
            role = msg['role']
            content = msg['content']
            if role == 'user':
                conversation.append(f"<|user|>\n{content}<|end|>")
            else:
                conversation.append(f"<|assistant|>\n{content}<|end|>")
        conversation.append("<|assistant|>")
        formatted = "\n".join(conversation)
        logger.debug(f"Formatted conversation length: {len(formatted)} characters")
        return formatted

    def print_messages_for_model(self, model_type: str) -> None:
        """Print the messages that will be sent to the model in a readable format."""
        logger.info(f"\n{'='*50}")
        logger.info(f"Messages being sent to {model_type} model:")
        logger.info(f"Total messages: {len(self.messages)}")
        logger.info(f"Total tokens: {self.get_token_count()}/{self.max_tokens}")
        logger.info(f"{'='*50}")
        
        for i, msg in enumerate(self.messages, 1):
            logger.info(f"\nMessage {i}:")
            logger.info(f"Role: {msg['role']}")
            logger.info(f"Content: {msg['content']}")
            logger.info(f"Tokens: {len(self.encoding.encode(msg['content']))}")
        
        logger.info(f"{'='*50}\n")

    def get_formatted_messages(self, model_type: str) -> str:
        """Get messages formatted for the specified model type."""
        logger.debug(f"Getting formatted messages for model type: {model_type}")
        
        # Print messages before formatting
        self.print_messages_for_model(model_type)
        
        if model_type == 'gemma':
            return self.format_for_gemma()
        elif model_type == 'gemma-3-4b-it-q6_k':
            return self.format_for_gemma3()
        elif model_type == 'phi':
            return self.format_for_phi()
        else:
            logger.error(f"Unknown model type: {model_type}")
            raise ValueError(f"Unknown model type: {model_type}")

    def __str__(self) -> str:
        """Return a string representation of the buffer contents."""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.messages]) 