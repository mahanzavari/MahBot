// State management
let currentChatId = null;
let apiKey = localStorage.getItem('apiKey') || '';
let useApi = true; // Always use API
let apiType = localStorage.getItem('apiType') || 'openai';
let searchModeEnabled = localStorage.getItem('searchModeEnabled') === 'true';

// DOM Elements
let messageInput;
let sendBtn;
let uploadBtn;
let imagePreview;
let messagesContainer;
let chatList;
let newChatBtn;
let chatSearch;
let themeToggle;
let apiKeyInput;
let apiTypeSelect;
let apiKeyModal;
let apiKeyInstructions;
let saveApiKeyBtn;
let cancelApiKeyBtn;
let imageUpload;
let currentImage = null;
let allChats = []; // Store all chats for filtering
let searchToggleBtn;

// Initialize DOM elements
function initializeDOMElements() {
    messageInput = document.getElementById('messageInput');
    sendBtn = document.getElementById('sendBtn');
    uploadBtn = document.getElementById('uploadBtn');
    imagePreview = document.getElementById('imagePreview');
    messagesContainer = document.querySelector('.messages');
    chatList = document.getElementById('chatList');
    newChatBtn = document.getElementById('newChatBtn');
    chatSearch = document.getElementById('chatSearch');
    themeToggle = document.getElementById('themeToggle');
    apiKeyInput = document.getElementById('apiKeyInput');
    apiTypeSelect = document.getElementById('apiType');
    apiKeyModal = document.getElementById('apiKeyModal');
    apiKeyInstructions = document.getElementById('apiKeyInstructions');
    saveApiKeyBtn = document.getElementById('saveApiKey');
    cancelApiKeyBtn = document.getElementById('cancelApiKey');
    imageUpload = document.getElementById('imageUpload');
    searchToggleBtn = document.getElementById('searchToggleBtn');
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initializeDOMElements();
    loadChats();
    setupEventListeners();
    updateSearchToggleState();
    // Show API key modal if no key is set
    if (apiKeyModal && !apiKey) {
        apiKeyModal.classList.add('active');
    }
});

function setupEventListeners() {
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            const imageInput = document.getElementById('imageInput');
            if (imageInput) imageInput.click();
        });
    }

    const imageInput = document.getElementById('imageInput');
    if (imageInput) {
        imageInput.addEventListener('change', handleImageUpload);
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }

    if (chatSearch) {
        chatSearch.addEventListener('input', filterChats);
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    if (apiTypeSelect) {
        apiTypeSelect.addEventListener('change', handleApiTypeChange);
    }

    if (saveApiKeyBtn) {
        saveApiKeyBtn.addEventListener('click', saveApiKey);
    }

    if (cancelApiKeyBtn) {
        cancelApiKeyBtn.addEventListener('click', () => {
            if (apiKeyModal) {
                apiKeyModal.classList.remove('active');
                if (apiKeyInput) apiKeyInput.value = ''; // Clear the input when canceling
                if (!apiKey) {
                    // If no API key is set, show the modal again after a short delay
                    setTimeout(() => {
                        apiKeyModal.classList.add('active');
                    }, 100);
                }
            }
        });
    }

    if (imageUpload) {
        imageUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && imagePreview) {
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

    if (searchToggleBtn) {
        searchToggleBtn.addEventListener('click', toggleSearchMode);
    }
}

// Initialize
loadChats();
apiTypeSelect.value = apiType;
updateApiKeyInstructions();

// Functions
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    if (!message) return;

    // Disable input and send button while processing
    messageInput.disabled = true;
    const sendButton = document.querySelector('.send-button');
    sendButton.disabled = true;

    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'message bot-message';
    typingIndicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    messagesContainer.appendChild(typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        // Create new chat if no current chat
        if (!currentChatId) {
            const response = await fetch('/api/chats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            currentChatId = data.id;
            
            // Update chat title in sidebar
            const chatTitle = message.length > 30 ? message.substring(0, 30) + '...' : message;
            await fetch(`/api/chats/${currentChatId}/title`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: chatTitle })
            });
        }

        // Send message to server
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId,
                model_type: document.getElementById('modelSelect').value,
                is_new_chat: false,
                use_search: searchModeEnabled
            })
        });

        // Remove typing indicator
        messagesContainer.removeChild(typingIndicator);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to send message');
        }

        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let botMessage = '';
        let botMessageElement = null;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (!line) continue;
                try {
                    const data = JSON.parse(line);
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }

                    if (data.response) {
                        if (!botMessageElement) {
                            botMessageElement = document.createElement('div');
                            botMessageElement.className = 'message bot-message';
                            if (data.used_search) {
                                botMessageElement.classList.add('search-enhanced');
                            }
                            messagesContainer.appendChild(botMessageElement);
                        }
                        botMessage += data.response;
                        botMessageElement.innerHTML = marked.parse(botMessage);
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }

                    if (data.token_count !== undefined) {
                        const tokenCount = document.getElementById('tokenCount');
                        if (tokenCount) {
                            tokenCount.textContent = `Tokens: ${data.token_count}/${data.max_tokens}`;
                        }
                    }

                    if (data.chat_id) {
                        currentChatId = data.chat_id;
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                }
            }
        }

        // Clear input and image preview
        messageInput.value = '';
        const imagePreview = document.getElementById('imagePreview');
        if (imagePreview) {
            imagePreview.style.display = 'none';
        }

        // Update chat list
        await loadChats();

    } catch (error) {
        console.error('Error:', error);
        alert(error.message);
    } finally {
        // Re-enable input and send button
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
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
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to create new chat');
        }
        
        currentChatId = data.id;
        
        // Clear messages container
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        
        // Add new chat to allChats array
        allChats.unshift({
            id: data.id,
            title: data.title,
            created_at: data.created_at
        });
        
        // Update sidebar
        await loadChats();
        
        // Focus on message input
        if (messageInput) {
            messageInput.focus();
        }

        return data.id;
    } catch (error) {
        console.error('Error creating new chat:', error);
        alert(`Failed to create new chat: ${error.message}`);
        throw error; // Re-throw to let caller handle the error
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

// Add function to handle new chat button click
function startNewChat() {
    currentChatId = null;
    messagesContainer.innerHTML = '';
    const tokenCount = document.getElementById('tokenCount');
    if (tokenCount) {
        tokenCount.textContent = 'Tokens: 0/64000';
    }
    
    // Send a message to clear the buffer
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: 'Starting new chat',
            chat_id: null,
            model_type: document.getElementById('modelSelect').value,
            is_new_chat: true  // Set to true when starting a new chat
        })
    }).catch(error => {
        console.error('Error starting new chat:', error);
    });
}

async function sendSearchQuery() {
    const messageInput = document.getElementById('messageInput');
    const query = messageInput.value.trim();

    if (!query) {
        alert('Please enter a search query.');
        return;
    }

    // Disable input and buttons while processing
    messageInput.disabled = true;
    searchToggleBtn.disabled = true;
    sendBtn.disabled = true;

    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'message bot-message';
    typingIndicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    messagesContainer.appendChild(typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        // Add user message to UI
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user-message';
        userMessageDiv.innerHTML = `<div class="message-content">Searching for: ${query}</div>`;
        messagesContainer.appendChild(userMessageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Clear input
        messageInput.value = '';

        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        });

        // Remove typing indicator
        messagesContainer.removeChild(typingIndicator);

        const data = await response.json();

        if (response.ok) {
            // Display search results
            let resultsContent = "Here's what I found:\n\n";
            data.results.forEach((result, index) => {
                resultsContent += `${index + 1}. **${result.source_title}**\n`;
                resultsContent += `   *Snippet:* ${result.snippet}\n`;
                resultsContent += `   *URL:* [${result.url}](${result.url})\n\n`;
            });

            const botMessageDiv = document.createElement('div');
            botMessageDiv.className = 'message bot-message';
            botMessageDiv.innerHTML = marked.parse(resultsContent);
            messagesContainer.appendChild(botMessageDiv);
        } else {
            const errorMessageDiv = document.createElement('div');
            errorMessageDiv.className = 'message bot-message';
            errorMessageDiv.innerHTML = `<div class="message-content">Error: ${data.error || 'Failed to perform search'}</div>`;
            messagesContainer.appendChild(errorMessageDiv);
        }
    } catch (error) {
        console.error('Error during search:', error);
        const errorMessageDiv = document.createElement('div');
        errorMessageDiv.className = 'message bot-message';
        errorMessageDiv.innerHTML = `<div class="message-content">Error: ${error.message || 'Failed to perform search'}</div>`;
        messagesContainer.appendChild(errorMessageDiv);
    } finally {
        // Re-enable input and buttons
        messageInput.disabled = false;
        searchToggleBtn.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

function toggleSearchMode() {
    searchModeEnabled = !searchModeEnabled;
    localStorage.setItem('searchModeEnabled', searchModeEnabled);
    updateSearchToggleState();
}

function updateSearchToggleState() {
    if (searchToggleBtn) {
        if (searchModeEnabled) {
            searchToggleBtn.classList.add('search-toggle-active');
            searchToggleBtn.querySelector('.search-indicator').style.display = 'block';
            messageInput.placeholder = 'Type your message (web search enabled)...';
        } else {
            searchToggleBtn.classList.remove('search-toggle-active');
            searchToggleBtn.querySelector('.search-indicator').style.display = 'none';
            messageInput.placeholder = 'Type your message...';
        }
    }
} 