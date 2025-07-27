// Chat Dialog JavaScript
class InterviewCoachChat {
    constructor() {
        this.currentQuestion = null;
        this.messages = [];
        this.isLoading = false;
        this.init();
    }

    init() {
        // Initialize event listeners
        this.setupEventListeners();
        this.setupAutoResize();
    }

    setupEventListeners() {
        // Chat input enter key
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Auto-resize textarea
            chatInput.addEventListener('input', () => {
                this.autoResizeTextarea(chatInput);
            });
        }

        // Close dialog on overlay click
        const overlay = document.getElementById('chatDialog');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.closeDialog();
                }
            });
        }
    }

    setupAutoResize() {
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            this.autoResizeTextarea(chatInput);
        }
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    openDialog(questionId, questionText) {
        this.currentQuestion = { id: questionId, text: questionText };
        this.messages = [];
        
        // Update question context
        const contextElement = document.getElementById('chatQuestionContext');
        if (contextElement) {
            contextElement.textContent = `Helping with: "${questionText}"`;
        }

        // Show dialog
        const dialog = document.getElementById('chatDialog');
        if (dialog) {
            dialog.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }

        // Clear messages
        this.clearMessages();

        // Add welcome message
        this.addAIMessage(`Hello! I'm your interview coach. I'm here to help you answer this question: "${questionText}"

What would you like to know about crafting your response? I can help you with:
• Structuring your answer
• Providing specific examples
• Avoiding common pitfalls
• Practicing your response

Feel free to ask me anything!`);

        // Focus on input
        setTimeout(() => {
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.focus();
            }
        }, 100);
    }

    closeDialog() {
        const dialog = document.getElementById('chatDialog');
        if (dialog) {
            dialog.style.display = 'none';
            document.body.style.overflow = ''; // Restore scrolling
        }
        this.currentQuestion = null;
        this.messages = [];
    }

    clearMessages() {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
    }

    addUserMessage(text) {
        const message = {
            type: 'user',
            text: text,
            timestamp: new Date()
        };
        this.messages.push(message);
        this.renderMessage(message);
    }

    addAIMessage(text) {
        const message = {
            type: 'ai',
            text: text,
            timestamp: new Date()
        };
        this.messages.push(message);
        this.renderMessage(message);
    }

    renderMessage(message) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${message.type}`;

        const avatar = document.createElement('div');
        avatar.className = 'chat-message-avatar';
        avatar.textContent = message.type === 'user' ? 'U' : 'AI';

        const content = document.createElement('div');
        content.className = 'chat-message-content';

        const text = document.createElement('p');
        text.className = 'chat-message-text';
        text.textContent = message.text;

        const time = document.createElement('div');
        time.className = 'chat-message-time';
        time.textContent = message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        content.appendChild(text);
        content.appendChild(time);
        messageElement.appendChild(avatar);
        messageElement.appendChild(content);
        messagesContainer.appendChild(messageElement);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const typingElement = document.createElement('div');
        typingElement.className = 'chat-message ai';
        typingElement.id = 'typing-indicator';

        const avatar = document.createElement('div');
        avatar.className = 'chat-message-avatar';
        avatar.textContent = 'AI';

        const content = document.createElement('div');
        content.className = 'chat-message-content';

        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'chat-typing-indicator';
        typingIndicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;

        content.appendChild(typingIndicator);
        typingElement.appendChild(avatar);
        typingElement.appendChild(content);
        messagesContainer.appendChild(typingElement);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async sendMessage(messageText = null) {
        if (this.isLoading) return;

        const chatInput = document.getElementById('chatInput');
        const text = messageText || (chatInput ? chatInput.value.trim() : '');

        if (!text) return;

        // Add user message
        this.addUserMessage(text);

        // Clear input
        if (chatInput) {
            chatInput.value = '';
            this.autoResizeTextarea(chatInput);
        }

        // Show typing indicator
        this.showTypingIndicator();
        this.isLoading = true;

        try {
            // Simulate AI response (replace with actual API call)
            const response = await this.getAIResponse(text);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add AI response
            this.addAIMessage(response);
        } catch (error) {
            console.error('Error getting AI response:', error);
            this.hideTypingIndicator();
            this.addAIMessage('Sorry, I encountered an error. Please try again.');
        } finally {
            this.isLoading = false;
        }
    }

    async getAIResponse(userMessage) {
        // TODO: Replace with actual AI API call
        // For now, return a mock response
        await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate API delay

        const responses = [
            "Great question! Here's how you can approach this: [AI guidance would go here]",
            "I'd recommend structuring your answer like this: [AI structure would go here]",
            "Here are some key points to include: [AI points would go here]",
            "Let me help you craft a strong response: [AI response would go here]"
        ];

        return responses[Math.floor(Math.random() * responses.length)];
    }
}

// Global chat instance
let interviewCoachChat = null;

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    interviewCoachChat = new InterviewCoachChat();
});

// Global functions for button onclick handlers
function openChatDialog(questionId, questionText) {
    if (interviewCoachChat) {
        interviewCoachChat.openDialog(questionId, questionText);
    }
}

function closeChatDialog() {
    if (interviewCoachChat) {
        interviewCoachChat.closeDialog();
    }
}

function sendChatMessage() {
    if (interviewCoachChat) {
        interviewCoachChat.sendMessage();
    }
}

function sendQuickMessage(message) {
    if (interviewCoachChat) {
        interviewCoachChat.sendMessage(message);
    }
} 