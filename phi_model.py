from llama_cpp import Llama
import os
from utils import check_gpu_availability
import logging

logger = logging.getLogger(__name__)

class PhiModel:
    def __init__(self):
        model_path = "models/phi-3-mini-4k-instruct-Q5_K_S.gguf"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please download it from Hugging Face.")
        
        try:
            # Check GPU availability
            gpu_config = check_gpu_availability()
            logger.info(f"Initializing Phi model with GPU config: {gpu_config}")
            
            self.llm = Llama(
                model_path=model_path,
                n_ctx=4096,  # Context window
                n_threads=4,  # Number of CPU threads to use
                n_gpu_layers=gpu_config['n_gpu_layers']  # Use GPU layers based on availability
            )
            logger.info(f"Phi model loaded successfully using {'GPU' if gpu_config['has_gpu'] else 'CPU'}")
        except Exception as e:
            logger.error(f"Error loading Phi model: {str(e)}")
            raise
        
        self.system_prompt = """You are a helpful AI assistant. 
        Provide accurate, concise, and helpful responses to legal questions. 
        do not proivde a long response unless you are told to.
        If you're unsure about something, acknowledge the limitations and suggest consulting a legal professional."""

    def generate_response(self, messages):
        if not self.llm:
            return "Error: Phi model is not loaded. Please check the model file and try again."
        
        try:
            # Format the conversation history using the buffer's formatting method
            from chat_buffer import ChatBuffer
            buffer = ChatBuffer()
            for msg in messages:
                buffer.add_message(msg['role'], msg['content'])
            prompt = buffer.format_for_phi()
            
            response = self.llm(
                prompt,
                max_tokens=1024,
                temperature=0.7,
                stop=["<|end|>", "<|user|>"],
                echo=False
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                generated_text = response['choices'][0]['text'].strip()
                # Clean up any remaining markers
                generated_text = generated_text.replace("<|user|>", "").replace("<|assistant|>", "").replace("<|end|>", "").strip()
                return generated_text
            else:
                return None
                
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None 