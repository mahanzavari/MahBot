# download_gemma3_q4_0.py
from huggingface_hub import hf_hub_download
import os

# 1. Your HF repo and filename
repo_id = "google/gemma-3-4b-it"
filename = "gemma-3-4b-it-qat-Q4_0.gguf"
local_dir = "C:/Users/ASUS/Desktop/AUT/AI/Deep learning/Generative AI/Proj/LegalQA-chatbot/models/gemma/gemma3-Q4_0"

# 2. Ensure local path exists
os.makedirs(local_dir, exist_ok=True)

# 3. Download
path = hf_hub_download(
    repo_id=repo_id,
    filename=filename,
    cache_dir=local_dir,       # downloaded file will live here
    library_name="gemma3-q4_0"
)

print(f"✅ Download complete: {path}")





