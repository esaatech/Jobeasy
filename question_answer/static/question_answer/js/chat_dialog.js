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
        this.addAIMessage(`# 🤖 Welcome to Your Interview Coach!

I'm here to help you ace your interview questions! I can see you're working on:

**"${questionText}"**

## How I Can Help You:

• **📋 Answer Structure** - Get guidance on how to organize your response
• **💡 Examples** - See specific examples and scenarios
• **⚠️ What to Avoid** - Learn common mistakes and how to avoid them
• **🎯 Practice Response** - Get a sample answer to practice with

## Quick Tips:
- Be specific and use concrete examples
- Structure your answers clearly
- Practice your responses out loud
- Stay confident and authentic

**Ready to get started?** Ask me anything about this question or use the quick action buttons below!`);

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

        const text = document.createElement('div');
        text.className = 'chat-message-text';
        
        // Render markdown for AI messages, plain text for user messages
        if (message.type === 'ai' && typeof marked !== 'undefined') {
            try {
                // Configure marked.js for safe rendering
                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    sanitize: false // We trust our AI responses
                });
                text.innerHTML = marked.parse(message.text);
            } catch (error) {
                console.warn('Markdown rendering failed, falling back to plain text:', error);
                text.textContent = message.text;
            }
        } else {
            text.textContent = message.text;
        }

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
        // Get real AI response from Django backend
        try {
            const response = await fetch('/qa/api/interview-coach/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify({
                    question_id: this.currentQuestion.id,
                    user_message: userMessage
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                return data.response;
            } else {
                throw new Error(data.error || 'Failed to get response');
            }
        } catch (error) {
            console.error('Error getting AI response:', error);
            return 'Sorry, I encountered an error. Please try again.';
        }
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