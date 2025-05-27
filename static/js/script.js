// State management
let currentChatId = null;
let apiKey = localStorage.getItem('apiKey') || '';
let useApi = true; // Always use API
let apiType = localStorage.getItem('apiType') || 'openai';

// DOM Elements
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const uploadBtn = document.getElementById('uploadBtn');
const imagePreview = document.getElementById('imagePreview');
const messagesContainer = document.querySelector('.messages');
const chatList = document.getElementById('chatList');
const newChatBtn = document.getElementById('newChatBtn');
const chatSearch = document.getElementById('chatSearch');
const themeToggle = document.getElementById('themeToggle');
const apiKeyInput = document.getElementById('apiKeyInput');
const apiTypeSelect = document.getElementById('apiType');
const apiKeyModal = document.getElementById('apiKeyModal');
const apiKeyInstructions = document.getElementById('apiKeyInstructions');
const saveApiKeyBtn = document.getElementById('saveApiKey');
const cancelApiKeyBtn = document.getElementById('cancelApiKey');
const imageUpload = document.getElementById('imageUpload');
let currentImage = null;
let allChats = []; // Store all chats for filtering

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadChats();
    setupEventListeners();
    // Show API key modal if no key is set
    if (!apiKey) {
        apiKeyModal.classList.add('active');
    }
});

function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    uploadBtn.addEventListener('click', () => document.getElementById('imageInput').click());
    document.getElementById('imageInput').addEventListener('change', handleImageUpload);
    newChatBtn.addEventListener('click', createNewChat);
    chatSearch.addEventListener('input', filterChats);
    themeToggle.addEventListener('click', toggleTheme);
    apiTypeSelect.addEventListener('change', handleApiTypeChange);
    saveApiKeyBtn.addEventListener('click', saveApiKey);
    cancelApiKeyBtn.addEventListener('click', () => {
        apiKeyModal.classList.remove('active');
        apiKeyInput.value = ''; // Clear the input when canceling
        if (!apiKey) {
            // If no API key is set, show the modal again after a short delay
            setTimeout(() => {
                apiKeyModal.classList.add('active');
            }, 100);
        }
    });
    imageUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.innerHTML = `
                    <img src="${e.target.result}" alt="Preview">
                    <button class="remove-image" onclick="removeImage()">×</button>
                `;
                imagePreview.style.display = 'block';
                currentImage = file;
            };
            reader.readAsDataURL(file);
        }
    });
}

// Initialize
loadChats();
apiTypeSelect.value = apiType;
updateApiKeyInstructions();

// Functions
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message && !currentImage) return;

    if (!apiKey) {
        apiKeyModal.classList.add('active');
        return;
    }

    if (!currentChatId) {
        await createNewChat();
    }

    // Add user message to UI
    addMessageToUI('user', message);
    messageInput.value = '';

    try {
        let response;
        if (currentImage) {
            // Handle image upload
            const formData = new FormData();
            formData.append('image', currentImage);
            response = await fetch('/api/upload-image', {
                method: 'POST',
                body: formData
            });
            const imageData = await response.json();
            
            if (!response.ok) {
                throw new Error(imageData.error || 'Failed to upload image');
            }

            // Send message with image
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message || 'Image uploaded',
                    chat_id: currentChatId,
                    api_key: apiKey,
                    use_api: true,
                    api_type: apiType,
                    image_data: imageData.image_data
                })
            });
        } else {
            // Send text-only message
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    chat_id: currentChatId,
                    api_key: apiKey,
                    use_api: true,
                    api_type: apiType
                })
            });
        }

        const data = await response.json();

        if (response.ok) {
            addMessageToUI('bot', data.response);
            // Clear image preview after successful send
            if (currentImage) {
                removeImage();
            }
            // Update chat list after successful message
            await loadChats();
            
            // Update the chat title in the sidebar if it's a new chat
            const chatItem = document.querySelector(`.chat-item[data-id="${currentChatId}"]`);
            if (chatItem && chatItem.querySelector('.chat-title').textContent === 'New Chat') {
                // Use first 30 characters of the message as title
                const title = message.length > 30 ? message.substring(0, 30) + '...' : message;
                await fetch(`/api/chats/${currentChatId}/title`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ title: title })
                });
                await loadChats(); // Reload to show updated title
            }
        } else {
            addMessageToUI('bot', `Error: ${data.error}`);
        }
    } catch (error) {
        addMessageToUI('bot', `Error: ${error.message || 'Failed to send message'}`);
        console.error('Error:', error);
    }
}

function addMessageToUI(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function createNewChat() {
    try {
        const response = await fetch('/api/chats', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to create new chat');
        }
        
        const data = await response.json();
        currentChatId = data.id;
        
        // Clear messages container
        messagesContainer.innerHTML = '';
        
        // Add new chat to allChats array
        allChats.unshift({
            id: data.id,
            title: 'New Chat',
            created_at: new Date().toISOString()
        });
        
        // Update sidebar
        await loadChats();
        
        // Focus on message input
        messageInput.focus();
    } catch (error) {
        console.error('Error creating new chat:', error);
        alert('Failed to create new chat. Please try again.');
    }
}

async function loadChats() {
    try {
        const response = await fetch('/api/chats');
        if (!response.ok) {
            throw new Error('Failed to load chats');
        }
        
        const data = await response.json();
        allChats = [];
        
        // Flatten and sort chats by date
        Object.values(data).forEach(group => {
            allChats.push(...group);
        });
        allChats.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        renderChats(allChats);
    } catch (error) {
        console.error('Error loading chats:', error);
    }
}

function renderChats(chats) {
    chatList.innerHTML = '';
    
    const groups = {
        'Today': [],
        'Yesterday': [],
        'Last 7 Days': [],
        'Last 30 Days': [],
        'Older': []
    };
    
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const lastWeek = new Date(now);
    lastWeek.setDate(lastWeek.getDate() - 7);
    const lastMonth = new Date(now);
    lastMonth.setDate(lastMonth.getDate() - 30);
    
    chats.forEach(chat => {
        const chatDate = new Date(chat.created_at);
        if (chatDate.toDateString() === now.toDateString()) {
            groups['Today'].push(chat);
        } else if (chatDate.toDateString() === yesterday.toDateString()) {
            groups['Yesterday'].push(chat);
        } else if (chatDate >= lastWeek) {
            groups['Last 7 Days'].push(chat);
        } else if (chatDate >= lastMonth) {
            groups['Last 30 Days'].push(chat);
        } else {
            groups['Older'].push(chat);
        }
    });
    
    Object.entries(groups).forEach(([group, groupChats]) => {
        if (groupChats.length > 0) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'chat-group';
            
            const groupTitle = document.createElement('div');
            groupTitle.className = 'chat-group-title';
            groupTitle.textContent = group;
            groupDiv.appendChild(groupTitle);
            
            groupChats.forEach(chat => {
                const chatItem = document.createElement('div');
                chatItem.className = 'chat-item';
                chatItem.dataset.id = chat.id;
                if (chat.id === currentChatId) {
                    chatItem.classList.add('active');
                }
                
                const chatTitle = document.createElement('div');
                chatTitle.className = 'chat-title';
                chatTitle.textContent = chat.title;
                
                const chatDate = document.createElement('div');
                chatDate.className = 'chat-date';
                chatDate.textContent = new Date(chat.created_at).toLocaleDateString();
                
                chatItem.appendChild(chatTitle);
                chatItem.appendChild(chatDate);
                
                chatItem.addEventListener('click', () => loadChat(chat.id));
                groupDiv.appendChild(chatItem);
            });
            
            chatList.appendChild(groupDiv);
        }
    });
}

async function loadChat(chatId) {
    try {
        const response = await fetch(`/api/chats/${chatId}`);
        if (!response.ok) {
            throw new Error('Failed to load chat');
        }
        
        const data = await response.json();
        currentChatId = chatId;
        
        // Update active state in sidebar
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.chat-item[data-id="${chatId}"]`).classList.add('active');
        
        // Clear and load messages
        messagesContainer.innerHTML = '';
        data.messages.forEach(msg => {
            addMessageToUI(msg.role, msg.content);
        });
    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

function filterChats() {
    const searchTerm = chatSearch.value.toLowerCase();
    const filteredChats = allChats.filter(chat => 
        chat.title.toLowerCase().includes(searchTerm) ||
        new Date(chat.created_at).toLocaleDateString().includes(searchTerm)
    );
    renderChats(filteredChats);
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        currentImage = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
}

function removeImage() {
    currentImage = null;
    imagePreview.src = '';
    imagePreview.style.display = 'none';
    document.getElementById('imageInput').value = '';
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

function handleApiTypeChange(e) {
    apiType = e.target.value;
    localStorage.setItem('apiType', apiType);
    updateApiKeyInstructions();
    
    // If we have a key, we should re-prompt for the correct type of key
    if (apiKey) {
        apiKey = '';
        localStorage.removeItem('apiKey');
        apiKeyModal.classList.add('active');
        apiKeyInput.focus();
    }
}

function updateApiKeyInstructions() {
    const instructions = {
        'openai': "Enter your OpenAI API key (starts with 'sk-')",
        'gemini': "Enter your Google Gemini API key"
    };
    apiKeyInstructions.textContent = instructions[apiType];
}

function saveApiKey() {
    apiKey = apiKeyInput.value.trim();
    if (apiKey) {
        localStorage.setItem('apiKey', apiKey);
        apiKeyModal.classList.remove('active');
        apiKeyInput.value = '';
    }
}

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme');
}

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
}); 