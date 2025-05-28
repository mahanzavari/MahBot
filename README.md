# Lysander - Legal AI Assistant

A modern web-based legal chatbot application that leverages multiple AI models to provide intelligent legal assistance. The application supports both local and cloud-based AI models, with features for chat history management, image analysis, and a beautiful, responsive user interface.

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

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd LegalQA-chatbot
```

2. Create a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
# Create PostgreSQL database
createdb MahBot_db

# Initialize database migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. Configure environment variables:
Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:your-password@localhost:5432/MahBot_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

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