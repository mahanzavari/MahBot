# AI Chatbot

A modern web-based chatbot application that supports both local and API-based responses, with features for chat history management and image uploads.

## Features

- Switch between local and API-based responses
- Chat history management
- Image upload support
- Context window management
- Modern, responsive UI
- Real-time message updates

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
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
   - Click "New Chat" to start a new conversation
   - Toggle between local and API mode using the switch
   - If using API mode, you'll be prompted to enter your API key
   - Type messages in the input box and press Enter or click Send
   - Upload images using the image upload button
   - View chat history in the sidebar

## API Mode

When using API mode, you'll need to provide an API key. The application currently supports the OpenAI API. Your API key is stored locally in your browser and is never sent to any server other than the API provider.

## Project Structure

```
.
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css  # Styles
│   └── js/
│       └── script.js  # Frontend logic
└── templates/
    └── index.html     # Main HTML template
```

## Security Notes

- API keys are stored in the browser's localStorage
- All API communications are done directly from the frontend to the API provider
- The backend server does not store or process API keys

## Contributing

Feel free to submit issues and enhancement requests! 