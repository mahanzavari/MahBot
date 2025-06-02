from llama_cpp import Llama
import os
from utils import check_gpu_availability
import logging

logger = logging.getLogger(__name__)

class GemmaModel:
    def __init__(self):
        model_path = "models/gemma-2b-it.Q4_K_M.gguf"
        
        if not os.path.exists(model_path):
            print("Warning: Gemma model not found. Please download the model:")
            print("- gemma-2b-it.Q4_K_M.gguf")
            print("\nPlace the model file in the 'models' directory.")
            self.llm = None
            return
        
        try:
            # Check GPU availability
            gpu_config = check_gpu_availability()
            logger.info(f"Initializing Gemma model with GPU config: {gpu_config}")
            
            self.llm = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_threads=4,
                n_batch=512,
                n_gpu_layers=gpu_config['n_gpu_layers'],
                verbose=True,
                embedding=False,
                rope_scaling=None
            )
            logger.info(f"Successfully loaded Gemma model from {model_path} using {'GPU' if gpu_config['has_gpu'] else 'CPU'}")
        except Exception as e:
            logger.error(f"Error loading Gemma model: {str(e)}")
            self.llm = None
        
        self.system_prompt = """You are a helpful and friendly AI assistant. You provide clear, accurate, and engaging responses to questions and tasks. 
        You maintain a conversational tone while being informative and precise. When you're unsure about something, you acknowledge it and suggest alternative approaches.
        do not proivde a long response unless you are told to.
        Always aim to be helpful, honest, and respectful in your responses."""

    def generate_response(self, messages):
        if not self.llm:
            return "Error: Gemma model is not loaded. Please check the model file and try again."
        
        try:
            # Format the conversation history using the buffer's formatting method
            from chat_buffer import ChatBuffer
            buffer = ChatBuffer()
            for msg in messages:
                buffer.add_message(msg['role'], msg['content'])
            full_prompt = buffer.format_for_gemma()
            
            response = self.llm(
                full_prompt,
                max_tokens=1024,
                temperature=0.7,
                stop=["<end_of_turn>", "<start_of_turn>"],
                echo=False
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                generated_text = response['choices'][0]['text'].strip()
                # Clean up any remaining markers
                generated_text = generated_text.replace("<start_of_turn>", "").replace("<end_of_turn>", "").strip()
                return generated_text
            else:
                return None
                
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None 