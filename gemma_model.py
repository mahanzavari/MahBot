from llama_cpp import Llama
import os

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
            self.llm = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_threads=4,
                n_batch=512
            )
            print(f"Successfully loaded Gemma model from {model_path}")
        except Exception as e:
            print(f"Error loading Gemma model: {str(e)}")
            self.llm = None
        
        self.system_prompt = """You are a helpful and friendly AI assistant. You provide clear, accurate, and engaging responses to questions and tasks. 
        You maintain a conversational tone while being informative and precise. When you're unsure about something, you acknowledge it and suggest alternative approaches.

        Always aim to be helpful, honest, and respectful in your responses."""

    def generate_response(self, prompt):
        if not self.llm:
            return "Error: Gemma model is not loaded. Please check the model file and try again."
        
        try:
            full_prompt = f"<start_of_turn>user\n{self.system_prompt}\n\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
            
            response = self.llm(
                full_prompt,
                max_tokens=1024,
                temperature=0.7,
                stop=["<end_of_turn>", "<start_of_turn>"],
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return f"Error: Failed to generate response. {str(e)}" 