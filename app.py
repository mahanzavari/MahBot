from flask import Flask, request, jsonify, render_template, url_for, Response, stream_with_context
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from flask_mail import Mail, Message
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import LLMChain
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
from gemma_3_model import Gemma3Model
from chat_buffer import ChatBuffer
import logging
from googlesearch import search as google_search
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
try:
    phi_model = PhiModel()
    logger.info("Phi model initialized successfully")
except Exception as e:
    logger.error(f"Failed to load Phi model: {str(e)}")
    phi_model = None

try:
    gemma_model = GemmaModel()
    logger.info("Gemma model initialized successfully")
except Exception as e:
    logger.error(f"Failed to load Gemma model: {str(e)}")
    gemma_model = None

try:
    gemma_3_model = Gemma3Model()
    logger.info("Gemma 3 model initialized successfully")
except Exception as e:
    logger.error(f"Failed to load Gemma 3 model: {str(e)}")
    gemma_3_model = None

# Store chat buffers for each user
chat_buffers = {}

# Register blueprints
app.register_blueprint(auth)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_user_buffer(user_id: int) -> ChatBuffer:
    """Get or create a chat buffer for a user."""
    if user_id not in chat_buffers:
        logger.debug(f"Creating new buffer for user {user_id}")
        chat_buffers[user_id] = ChatBuffer()
    else:
        logger.debug(f"Retrieved existing buffer for user {user_id}")
    return chat_buffers[user_id]

def print_buffer_contents(buffer: ChatBuffer, user_id: int, stage: str = ""):
    """Print the current contents of the chat buffer with additional debugging info."""
    logger.debug(f"\n{'='*50}")
    logger.debug(f"Buffer State - {stage}")
    logger.debug(f"User ID: {user_id}")
    logger.debug(f"Buffer ID: {id(buffer)}")
    logger.debug(f"Total Messages: {len(buffer.messages)}")
    logger.debug(f"Token Count: {buffer.get_token_count()}/{buffer.max_tokens}")
    logger.debug(f"Buffer Contents:")
    
    for i, msg in enumerate(buffer.messages, 1):
        logger.debug(f"\nMessage {i}:")
        logger.debug(f"Role: {msg['role']}")
        logger.debug(f"Content: {msg['content']}")
        logger.debug(f"Tokens: {len(buffer.encoding.encode(msg['content']))}")
    
    logger.debug(f"{'='*50}\n")

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
        message = data.get('message')
        chat_id_from_request = data.get('chat_id') # Renamed to avoid conflict with inner scope
        model_type = data.get('model_type', 'gemma')
        is_new_chat = data.get('is_new_chat', False)
        frontend_use_search = data.get('use_search', False) # For non-RAG models

        logger.info(f"Received chat request - User: {current_user.id}, Chat ID: {chat_id_from_request}, Model: {model_type}, New Chat: {is_new_chat}, Frontend Use Search: {frontend_use_search}")
        logger.debug(f"Message content: {message}")

        if not message:
            logger.warning("No message provided in request")
            return jsonify({'error': 'No message provided'}), 400

        buffer = get_user_buffer(current_user.id)

        # Buffer and chat history loading logic (simplified for brevity, ensure it's correct)
        current_chat_id_for_db = chat_id_from_request # Use this for DB operations initially
        if is_new_chat:
            logger.info(f"Starting new chat for user {current_user.id}")
            buffer.clear()
            current_chat_id_for_db = None # New chat will get ID after first message
            print_buffer_contents(buffer, current_user.id, "New Chat - Buffer Cleared")
        elif current_chat_id_for_db and not buffer.messages:
            chat_db_obj = Chat.query.get(current_chat_id_for_db)
            if chat_db_obj and chat_db_obj.user_id == current_user.id:
                if not buffer.load_from_db_messages(chat_db_obj.messages): # Error handling for long history
                    # ... (return error as in your original code) ...
                    pass
                    print_buffer_contents(buffer, current_user.id, "Loaded Existing Chat")

        print_buffer_contents(buffer, current_user.id, "Before Adding User Message")

        if not buffer.add_message('user', message): # Add current user message to buffer
            # ... (return error as in your original code for token limit) ...
            pass
        print_buffer_contents(buffer, current_user.id, "After Adding User Message")

        def generate_response_stream():
            nonlocal current_chat_id_for_db # To update if a new chat is created

            messages_for_model_context = buffer.get_messages()
            user_query = message # The most recent message is the primary query for RAG

            logger.info(f"Generating response for user {current_user.id} with query: '{user_query}' using model: {model_type}")
            response_text = ""
            used_search_internally = False

            if model_type == 'gemini-langchain':
                try:
                    gemini_api_key = os.environ.get('GEMINI_API_KEY') or app.config.get('GEMINI_API_KEY')
                    if not gemini_api_key:
                        raise ValueError("GEMINI_API_KEY not found.")

                    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=gemini_api_key, temperature=0.7)

                    # 1. Confidence Check
                    confidence_prompt = ChatPromptTemplate.from_messages([
                        SystemMessagePromptTemplate.from_template(
                            "You are an AI assistant. Your task is to determine if you can answer the user's query confidently and accurately from your own internal knowledge without needing external search. "
                            "Analyze the query for specificity, need for real-time data, or niche topics. "
                            "Respond with only 'yes' or 'no'."
                        ),
                        HumanMessagePromptTemplate.from_template("User query: '{user_query}'\nCan you answer this confidently from your own knowledge without search?")
                    ])
                    confidence_chain = LLMChain(llm=llm, prompt=confidence_prompt, output_parser=StrOutputParser())
                    logger.info("RAG: Performing confidence check.")
                    confidence_result = confidence_chain.invoke({"user_query": user_query}).strip().lower()
                    logger.info(f"RAG: Confidence check result: '{confidence_result}'")

                    if confidence_result == 'yes':
                        logger.info("RAG: Confident. Answering directly.")
                        direct_answer_prompt = ChatPromptTemplate.from_messages([
                            SystemMessagePromptTemplate.from_template("You are a helpful AI assistant. Answer the user's query clearly and concisely."),
                            HumanMessagePromptTemplate.from_template("{user_query}")
                        ])
                        answer_chain = LLMChain(llm=llm, prompt=direct_answer_prompt, output_parser=StrOutputParser())
                        response_text = answer_chain.invoke({"user_query": user_query})
                    else:
                        logger.info("RAG: Not confident. Proceeding to search.")
                        used_search_internally = True

                        # 2a. Transform query for search
                        search_query_prompt = ChatPromptTemplate.from_messages([
                            SystemMessagePromptTemplate.from_template(
                                "You are an AI assistant. Transform the user's query into a clear, precise search query for a search engine. "
                                "Focus on keywords and rephrase ambiguities. Return only the generated search query."
                            ),
                            HumanMessagePromptTemplate.from_template("Original user query: '{user_query}'\nGenerated search query:")
                        ])
                        search_query_chain = LLMChain(llm=llm, prompt=search_query_prompt, output_parser=StrOutputParser())
                        generated_search_query = search_query_chain.invoke({"user_query": user_query}).strip()
                        logger.info(f"RAG: Generated search query: '{generated_search_query}'")

                        # 2b. Perform Search (using existing app's search functionality)
                        search_results_snippets = []
                        if generated_search_query:
                            try:
                                for url in google_search(generated_search_query, num=3): # Max 3 results for context
                                    # ... (your existing search result fetching and parsing logic) ...
                                    # For example:
                                    search_page_response = requests.get(url, timeout=5)
                                    if search_page_response.status_code == 200:
                                        soup = BeautifulSoup(search_page_response.text, 'html.parser')
                                        title = soup.title.string if soup.title else url
                                        snippet_text = ""
                                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                                        if meta_desc and meta_desc.get('content'): 
                                            snippet_text = meta_desc['content']
                                        else:
                                            first_p = soup.find('p')
                                            if first_p: 
                                                snippet_text = first_p.get_text()
                                        snippet_text = re.sub(r'\s+', ' ', snippet_text).strip()[:250] + '...' if snippet_text else 'Snippet not available.'
                                        search_results_snippets.append(f"Title: {title}\nSnippet: {snippet_text}\nURL: {url}")
                            except Exception as e_search_item:
                                logger.error(f"RAG: Error processing search result {url}: {str(e_search_item)}")

                        search_context_str = "No relevant search results found."
                        if search_results_snippets:
                            search_context_str = "Relevant search results:\n\n" + "\n\n".join(search_results_snippets)
                        logger.debug(f"RAG: Search context: {search_context_str}")

                        # 2c. Synthesize Answer
                        synthesis_prompt = ChatPromptTemplate.from_messages([
                            SystemMessagePromptTemplate.from_template(
                                "You are a helpful AI assistant. Synthesize the provided search results to answer the user's query. "
                                "Integrate these facts into a coherent, contextually appropriate response. "
                                "If search results are insufficient or irrelevant, state that and answer based on your general knowledge if possible, noting the information couldn't be verified by search. "
                                "Do not return raw search results."
                            ),
                            HumanMessagePromptTemplate.from_template(
                                "User Query: '{user_query}'\n\nSearch Results:\n{search_context}\n\nSynthesized Answer:"
                            )
                        ])
                        synthesis_chain = LLMChain(llm=llm, prompt=synthesis_prompt, output_parser=StrOutputParser())
                        response_text = synthesis_chain.invoke({
                            "user_query": user_query,
                            "search_context": search_context_str
                        })

                    if not response_text:
                        response_text = "I encountered an issue with the RAG process and could not generate a response."

                except Exception as e_rag_main:
                    logger.error(f"Error in Gemini RAG system: {str(e_rag_main)}", exc_info=True)
                    yield json.dumps({'error': f'Gemini RAG error: {str(e_rag_main)}'}) + '\n'
                    return

            # --- Existing logic for local models ---
            elif model_type == 'gemma':
                if not gemma_model: # Check if model is loaded
                    # ... (yield error)
                    return
                logger.info("Using local Gemma model")
                # If frontend_use_search is true, you might want to prepend search results to messages_for_model_context
                # This part of your original code needs to be adapted if local models should also use search.
                # For now, it's separate from RAG.
                if frontend_use_search:
                    # (Your existing search logic for local models if any)
                    logger.info("Frontend search enabled for Gemma")
                response_text = gemma_model.generate_response(messages_for_model_context)
                used_search_internally = frontend_use_search # Reflects frontend's search toggle for these models

            elif model_type == 'gemma-3-4b-it-q6_k':
                # ... (similar logic for gemma_3_model)
                if not gemma_3_model: # Check if model is loaded
                     # ... (yield error)
                    return
                logger.info("Using local Gemma 3 model")
                if frontend_use_search:
                    logger.info("Frontend search enabled for Gemma 3")
                response_text = gemma_3_model.generate_response(messages_for_model_context)
                used_search_internally = frontend_use_search

            elif model_type == 'phi':
                # ... (similar logic for phi_model)
                if not phi_model: # Check if model is loaded
                     # ... (yield error)
                    return
                logger.info("Using local Phi model")
                if frontend_use_search:
                    logger.info("Frontend search enabled for Phi")
                response_text = phi_model.generate_response(messages_for_model_context)
                used_search_internally = frontend_use_search
            else:
                logger.error(f"Invalid model type: {model_type}")
                yield json.dumps({'error': 'Invalid model type'}) + '\n'
                return

            if response_text is None: # Ensure response_text has a value
                response_text = "I am unable to provide a response at this moment."

            logger.info(f"Model Response (first 100 chars): {response_text[:100]}...")

            if not buffer.add_message('assistant', response_text):
                # ... (handle token limit for response) ...
                pass
            print_buffer_contents(buffer, current_user.id, "After Adding Model Response")

            # --- Database Saving Logic ---
            # (Ensure chat_id is correctly handled whether it's new or existing)
            final_chat_id_for_response = current_chat_id_for_db
            if not final_chat_id_for_response: # If it was a new chat, create DB entry
                logger.info("Creating new chat in DB")
                chat_title = message[:50] + '...' if len(message) > 50 else message
                new_chat_db = Chat(title=chat_title, user_id=current_user.id)
                db.session.add(new_chat_db)
                db.session.flush() # To get ID for messages
                final_chat_id_for_response = new_chat_db.id

                # Add messages to this new chat
                msg_user_db = Message(content=message, role='user', chat_id=final_chat_id_for_response)
                msg_assistant_db = Message(content=response_text, role='assistant', chat_id=final_chat_id_for_response)
                db.session.add_all([msg_user_db, msg_assistant_db])
                db.session.commit()
                logger.info(f"Created new chat with ID: {final_chat_id_for_response}")
            else: # Existing chat
                chat_to_update = Chat.query.get(final_chat_id_for_response)
                if chat_to_update:
                    logger.info(f"Updating existing chat {final_chat_id_for_response}")
                    # User message was already added to buffer, DB entry for user msg should ideally be here too
                    # If your buffer.add_message doesn't save, save user message now
                    # Assuming user message for DB is the original 'message'
                    # msg_user_db = Message(content=message, role='user', chat_id=final_chat_id_for_response)
                    # db.session.add(msg_user_db) # Only if not saved earlier per user interaction

                    msg_assistant_db = Message(content=response_text, role='assistant', chat_id=final_chat_id_for_response)
                    db.session.add(msg_assistant_db)
                    chat_to_update.updated_at = datetime.now(UTC)
                    db.session.commit()

            yield json.dumps({
                'response': response_text,
                'chat_id': final_chat_id_for_response, # Use the definitive chat ID
                'token_count': buffer.get_token_count(),
                'max_tokens': buffer.max_tokens,
                'used_search': used_search_internally
            }) + '\n'

        return Response(stream_with_context(generate_response_stream()), mimetype='application/x-ndjson')

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
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

@app.route('/api/chats', methods=['POST'])
@login_required
def create_chat():
    try:
        # Create new chat
        chat = Chat(
            title='New Chat',
            user_id=current_user.id
        )
        db.session.add(chat)
        db.session.commit()
        
        return jsonify({
            'id': chat.id,
            'title': chat.title,
            'created_at': chat.created_at.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/search', methods=['POST'])
@login_required
def perform_search():
    try:
        data = request.get_json()
        query = data.get('query')

        if not query:
            return jsonify({'error': 'No search query provided'}), 400

        # Perform Google search
        search_results = []
        try:
            # Get top 5 search results
            for url in google_search(query, num=5):
                try:
                    # Fetch the webpage content
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Get title
                        title = soup.title.string if soup.title else url
                        
                        # Get snippet (first paragraph or meta description)
                        snippet = ''
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if meta_desc and meta_desc.get('content'):
                            snippet = meta_desc['content']
                        else:
                            # Find first paragraph
                            first_p = soup.find('p')
                            if first_p:
                                snippet = first_p.get_text()
                        
                        # Clean up snippet
                        snippet = re.sub(r'\s+', ' ', snippet).strip()
                        if len(snippet) > 200:
                            snippet = snippet[:197] + '...'
                        
                        search_results.append({
                            'source_title': title,
                            'snippet': snippet,
                            'url': url
                        })
                except Exception as e:
                    logger.error(f"Error processing search result {url}: {str(e)}")
                    continue

            if search_results:
                return jsonify({'results': search_results})
            else:
                return jsonify({'error': 'No results found'}), 404

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return jsonify({'error': f"Search failed: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True) 