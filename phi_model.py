from llama_cpp import Llama
import os

class PhiModel:
    def __init__(self):
        model_path = "models/phi-3-mini-4k-instruct-Q5_K_S.gguf"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please download it from Hugging Face.")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,  # Context window
            n_threads=4,  # Number of CPU threads to use
            n_gpu_layers=0  # Number of layers to offload to GPU
        )
        
        self.system_prompt = """You are a helpful AI assistant for a legal Q&A chatbot. 
        Provide accurate, concise, and helpful responses to legal questions. 
        If you're unsure about something, acknowledge the limitations and suggest consulting a legal professional."""

    def format_prompt(self, user_query):
        return f"""<|user|> 
{self.system_prompt}<|end|> 
<|assistant|> 
<|user|> 
{user_query}<|end|> 
<|assistant|>"""

    def generate_response(self, user_query):
        prompt = self.format_prompt(user_query)
        
        response = self.llm(
            prompt,
            max_tokens=512,
            temperature=0.7,
            top_p=0.95,
            stop=["<|end|>", "<|user|>"],
            echo=False
        )
        
        return response['choices'][0]['text'].strip() 