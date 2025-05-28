import os
from typing import Optional
from llama_cpp import Llama

class Gemma3Model:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), "models", "gemma-3-4b-it-q6_k.gguf")
        self.model = None
        self.load_model()

    def load_model(self):
        """Load the Gemma 3 4B IT Q6_K model using llama-cpp."""
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,  # Context window
                n_threads=4,  # Number of CPU threads to use
                n_gpu_layers=-1  # Use GPU for all layers if available
            )
            print(f"Gemma 3 4B IT Q6_K model loaded successfully")
        except Exception as e:
            print(f"Error loading Gemma 3 4B IT Q6_K model: {str(e)}")
            raise

    def generate_response(self, messages: list, max_length: int = 2048) -> Optional[str]:
        """Generate a response using the Gemma 3 4B IT Q6_K model."""
        try:
            if not self.model:
                raise ValueError("Model not loaded")

            # Format the conversation history using the buffer's formatting method
            from chat_buffer import ChatBuffer
            buffer = ChatBuffer()
            for msg in messages:
                buffer.add_message(msg['role'], msg['content'])
            formatted_prompt = buffer.format_for_gemma3()
            print(formatted_prompt)
            # Generate response
            response = self.model(
                formatted_prompt,
                max_tokens=max_length,
                temperature=0.7,
                top_p=0.9,
                stop=["<|end|>", "<|user|>"],
                echo=False
            )

            # Extract and clean the response
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

    def __del__(self):
        """Clean up resources when the model is deleted."""
        if hasattr(self, 'model'):
            del self.model 