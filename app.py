from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from flask_mail import Mail, Message
import os
import json
import requests
from datetime import datetime, timedelta, UTC
from PIL import Image
import io
import base64
import google.generativeai as genai
from models import db, User, Chat, Message
from config import Config
from auth import auth
from utils import send_verification_email
from phi_model import PhiModel
from gemma_model import GemmaModel

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app)
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Initialize models
phi_model = PhiModel()
gemma_model = GemmaModel()

# Register blueprints
app.register_blueprint(auth)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

def get_openai_response(messages, api_key):
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': m['role'], 'content': m['content']} 
                       for m in messages]
        }
    )
    response_data = response.json()
    
    if 'error' in response_data:
        raise Exception(f"OpenAI API Error: {response_data['error']['message']}")
    
    if not response_data.get('choices') or not response_data['choices'][0].get('message'):
        raise Exception('Invalid response format from OpenAI API')
    
    return response_data['choices'][0]['message']['content']

def get_gemini_response(messages, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Convert messages to Gemini format
        chat = model.start_chat(history=[])
        for msg in messages:
            if msg['role'] == 'user':
                chat.send_message(msg['content'])
            else:
                # For assistant messages, we'll just store them in history
                pass
        
        response = chat.last.text
        return response
    except Exception as e:
        raise Exception(f"Gemini API Error: {str(e)}")

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        chat_id = data.get('chat_id')
        model_type = data.get('model_type', 'gemma')  # Default to Gemma model
        api_key = data.get('api_key')

        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Get or create chat
        chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if not chat:
            chat = Chat(id=chat_id, user_id=current_user.id, title='New Chat')
            db.session.add(chat)
            db.session.commit()

        # Save user message
        user_message = Message(
            chat_id=chat.id,
            role='user',
            content=message
        )
        db.session.add(user_message)

        # Get chat history
        chat_history = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp).all()
        messages = [{'role': msg.role, 'content': msg.content} for msg in chat_history]

        # Process with selected model
        if model_type == 'gemma':
            response = gemma_model.generate_response(message)
        elif model_type == 'phi':
            response = phi_model.generate_response(message)
        elif model_type == 'openai':
            if not api_key:
                return jsonify({'error': 'API key is required for OpenAI'}), 400
            response = get_openai_response(messages, api_key)
        else:  # gemini
            if not api_key:
                return jsonify({'error': 'API key is required for Gemini'}), 400
            response = get_gemini_response(messages, api_key)

        # Save bot response
        bot_message = Message(
            chat_id=chat.id,
            role='bot',
            content=response
        )
        db.session.add(bot_message)
        db.session.commit()

        return jsonify({'response': response})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chats/<chat_id>/title', methods=['PUT'])
@login_required
def update_chat_title(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    new_title = data.get('title', 'New Chat')
    chat.title = new_title
    db.session.commit()
    return jsonify({'message': 'Title updated successfully'})

@app.route('/api/chats', methods=['GET'])
@login_required
def get_chats():
    now = datetime.now(UTC)
    today = now.date()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    
    grouped_chats = {
        'today': [],
        'yesterday': [],
        'last_week': [],
        'last_month': [],
        'older': []
    }
    
    for chat in chats:
        chat_date = chat.created_at.date()
        chat_data = {
            'id': chat.id,
            'title': chat.title,
            'created_at': chat.created_at.isoformat(),
            'message_count': len(chat.messages)
        }
        
        if chat_date == today:
            grouped_chats['today'].append(chat_data)
        elif chat_date == yesterday:
            grouped_chats['yesterday'].append(chat_data)
        elif chat_date >= last_week:
            grouped_chats['last_week'].append(chat_data)
        elif chat_date >= last_month:
            grouped_chats['last_month'].append(chat_data)
        else:
            grouped_chats['older'].append(chat_data)
    
    return jsonify(grouped_chats)

@app.route('/api/chats/<chat_id>', methods=['GET'])
@login_required
def get_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'messages': [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in chat.messages
        ]
    })

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(chat)
    db.session.commit()
    return jsonify({'message': 'Chat deleted successfully'})

@app.route('/api/upload-image', methods=['POST'])
@login_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Read and validate image
        img = Image.open(file.stream)
        # Convert to base64 for storage/transmission
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image_data': img_str
        })
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/api/chats', methods=['DELETE'])
@login_required
def clear_chats():
    try:
        # Delete all chats for the current user
        Chat.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'message': 'Chat history cleared successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 