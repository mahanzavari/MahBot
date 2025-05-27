from llama_cpp import Llama
import os

class GemmaModel:
    def __init__(self):
        model_path = "models/gemma-2b-it-q4_k_m.gguf"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Gemma model not found at {model_path}")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4
        )
        
        self.system_prompt = """You are a helpful AI assistant specialized in legal matters. 
        You provide clear, accurate, and professional responses to legal questions. 
        Always maintain a professional tone and clarify when you're unsure about something."""

    def generate_response(self, prompt):
        full_prompt = f"<bos><start_of_turn>user\n{self.system_prompt}\n\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        
        response = self.llm(
            full_prompt,
            max_tokens=1024,
            temperature=0.7,
            stop=["<end_of_turn>", "<start_of_turn>"],
            echo=False
        )
        
        return response['choices'][0]['text'].strip() 