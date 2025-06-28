# Calliope  - Legal AI Assistant

A modern web-based legal chatbot application that leverages multiple AI models to provide intelligent legal assistance. The application supports both local and cloud-based AI models, with features for chat history management, image analysis, and a beautiful, responsive user interface.

![Screenshot from Calliope Chat screen](stuff\image.png)

## Features

- Multiple AI Model Support:
  - GEMMA Models:
    - Gemma 2B
    - Gemma 3 4B IT Q6_K
  - PHI Models:
    - Phi-3
- User Authentication System
- Chat History Management
- Image Upload and Analysis (coming soon, **not implemented**)
- Modern, Responsive UI with Dark/Light Mode
- Real-time Message Updates
- Secure API Key Management

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL Database
- Git
- CUDA-capable GPU (optional, for GPU acceleration)

### GPU Support
The application supports GPU acceleration for faster model inference. To enable GPU support:

1. Install CUDA Toolkit (if not already installed):
   - Windows: Download from [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
   - Linux: 
     ```bash
     sudo apt-get update
     sudo apt-get install nvidia-cuda-toolkit
     ```

2. Install GPU dependencies:
   ```bash
   # Uncomment GPU-related packages in requirements.txt
   # Then run:
   pip install -r requirements.txt
   ```

3. Verify GPU detection:
   ```bash
   python -c "import torch; print('GPU Available:', torch.cuda.is_available())"
   ```

The application will automatically detect GPU availability and use it for model inference if available. If no GPU is detected, it will fall back to CPU inference.

### Linux-specific Prerequisites
- Build essentials (for some Python packages):
  ```bash
  sudo apt-get update
  sudo apt-get install build-essential python3-dev
  ```
- PostgreSQL installation:
  ```bash
  sudo apt-get install postgresql postgresql-contrib
  ```
- Additional system dependencies:
  ```bash
  sudo apt-get install libpq-dev
  ```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd LegalQA-chatbot
```

2. Create a virtual environment:
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On Linux/MacOS:
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

4. Set up the database:
```bash
# On Windows:
# Create PostgreSQL database using pgAdmin or command line
createdb MahBot_db

# On Linux:
# Create PostgreSQL user and database
sudo -u postgres psql
postgres=# CREATE USER your_username WITH PASSWORD 'your_password';
postgres=# CREATE DATABASE MahBot_db;
postgres=# GRANT ALL PRIVILEGES ON DATABASE MahBot_db TO your_username;
postgres=# \q

# Initialize database migrations (after setting up the database)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. Configure environment variables:
Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/MahBot_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

6. Set up file permissions (Linux/MacOS):
```bash
# Make sure the application has proper permissions
chmod +x app.py
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Access the Chatbot:

### Local Access
Open your web browser and navigate to:
```
http://localhost:5000
```

### Same Network Access
To access the chatbot from other devices on the same network (like your phone):

1. Find your computer's local IP address:
   ```bash
   # On Windows:
   ipconfig
   # Look for "IPv4 Address" under your active network adapter
   
   # On Mac/Linux:
   ifconfig
   # or
   ip addr
   # Look for "inet" followed by your IP address
   ```

2. Start the Flask server with host parameter:
   ```bash
   python app.py --host=0.0.0.0
   ```

3. On your mobile device, open a web browser and enter:
   ```
   http://YOUR_COMPUTER_IP:5000
   ```
   Replace YOUR_COMPUTER_IP with the IP address you found in step 1.

Note: Make sure your computer's firewall allows incoming connections on port 5000.

### Internet Access (Development/Testing)
To access the chatbot from other devices (like your phone) during development:

1. Install ngrok:
```bash
# Using pip
pip install pyngrok

# Or download from https://ngrok.com/download
```

2. Start ngrok to create a tunnel:
```bash
ngrok http 5000
```

3. Use the provided ngrok URL (e.g., `https://xxxx-xx-xx-xxx-xx.ngrok.io`) to access your chatbot from any device.

### Production Deployment
For production deployment, you have several options:

1. **Cloud Platforms**:
   - Heroku
   - Google Cloud Platform
   - AWS
   - DigitalOcean
   - Azure

2. **VPS (Virtual Private Server)**:
   - Set up a VPS with providers like DigitalOcean, Linode, or Vultr
   - Configure a domain name
   - Set up SSL certificates
   - Use a production-grade WSGI server like Gunicorn
   - Use Nginx as a reverse proxy

3. **Docker Deployment**:
   - Containerize the application
   - Deploy using Docker Compose
   - Use container orchestration services

For detailed deployment instructions, please refer to the deployment documentation in the `docs` folder.

### Google Colab Deployment
To run this project on Google Colab:

1. Open Google Colab (https://colab.research.google.com)

2. Clone the repository and run the setup script:
```python
# Clone the repository
!git clone <repository-url>
%cd LegalQA-chatbot

# Run the Colab setup script
!python run_colab.py
```

The script will:
- Install all required system dependencies
- Set up PostgreSQL database
- Install Python packages
- Configure environment variables
- Initialize the database
- Set up ngrok for external access
- Start the Flask application

Important Notes for Colab:
- Colab sessions are temporary and will reset when disconnected
- Save your database and important data to Google Drive
- The ngrok URL will change each time you restart the notebook
- Some features might be limited due to Colab's environment restrictions
- GPU acceleration is available but not required for this application
- Make sure to update the email configuration in the .env file with your actual email settings

To use GPU acceleration in Colab:
```Bash
%cd MahBot
!mkdir models

!wget https://huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct-Q5_K_S.gguf -O /content/MahBot/models/Phi-3-mini-4k-instruct-Q5_K_S.gguf
!wget https://huggingface.co/codegood/gemma-2b-it-Q4_K_M-GGUF/resolve/main/gemma-2b-it.Q4_K_M.gguf -O /content/MahBot/models/gemma-2b-it.Q4_K_M.gguf
!wget https://huggingface.co/Triangle104/gemma-3-4b-it-Q6_K-GGUF/resolve/main/gemma-3-4b-it-q6_k.gguf -O /content/MahBot/models/gemma-3-4b-it-q6_k.gguf
```
1. Go to Runtime > Change runtime type
2. Select "GPU" as the Hardware accelerator
3. The application will automatically detect and use the GPU if available

3. Using the Chatbot:
   - Register/Login to your account
   - Select your preferred AI model from the dropdown
   - Click "New Chat" to start a new conversation
   - Type your legal questions in the input box
   - Upload relevant documents/images using the upload button
   - View and manage your chat history in the sidebar
   - Toggle between dark and light themes using the theme button

## Model Information

### GEMMA Models
- **Gemma 2B**: A lightweight model suitable for quick responses
- **Gemma 3 4B IT Q6_K**: A more powerful model with improved performance

### PHI Models
- **Phi-3**: Microsoft's latest model optimized for legal and technical content

## Project Structure

```
.
├── app.py              # Flask backend
├── models.py           # Database models
├── config.py           # Configuration settings
├── auth.py            # Authentication routes
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css  # Styles
│   └── js/
│       └── script.js  # Frontend logic
└── templates/
    └── index.html     # Main HTML template
```

## Security Features

- Secure user authentication
- Password hashing
- Email verification system
- API key management
- Session management
- CSRF protection

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask and its extensions
- PostgreSQL
- The AI model providers (Google, Microsoft)
- All contributors and users of the project 