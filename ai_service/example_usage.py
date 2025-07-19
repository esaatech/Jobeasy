"""
Example usage of AI Resume Assistant with proper user management

This file demonstrates how to integrate the AI assistant with Django views
and handle user authentication properly.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

from .ai_resume_assistant import OpenAIAssistantManager

logger = logging.getLogger(__name__)

# Global assistant manager instance (could be cached or stored in settings)
assistant_manager = None
assistant_id = None

def get_or_create_assistant():
    """Get or create the resume builder assistant"""
    global assistant_manager, assistant_id
    
    if assistant_manager is None:
        assistant_manager = OpenAIAssistantManager()
        
        # Create assistant with all resume functions
        from .task_schema import TASK_SCHEMAS
        from .ai_resume_assistant import FunctionConfig
        
        # Create all function configurations
        functions = []
        for function_name, schema in TASK_SCHEMAS['resume'].items():
            function_config = FunctionConfig(
                name=schema['name'],
                description=schema['description'],
                parameters=schema['parameters'],
                instructions=f"Use this function when {schema['description'].lower()}"
            )
            functions.append(function_config)
        
        # Create the assistant
        assistant_id = assistant_manager.create_assistant(
            name="Resume Builder Assistant",
            base_instructions="""You are a friendly and professional resume builder assistant.
            
            Your role is to guide users through creating their resume step by step in a conversational manner.
            
            RESUME MANAGEMENT:
            - When a user wants to create a resume, first use create_resume function
            - Always use the resume_id returned from create_resume for all subsequent operations
            - If user wants to edit existing resumes, use list_user_resumes
            - Use get_resume_info to check the current state of a resume
            
            TEMPLATE HANDLING:
            - When users ask about templates, use the list_templates function to show available options
            - When users want to switch templates, use the switch_template function with the resume_id
            - Help users choose the best template for their industry and experience level
            
            RESUME BUILDING FLOW:
            1. Create resume first (create_resume)
            2. Save personal information (save_personal_info)
            3. Add work experience entries (save_experience)
            4. Add education entries (save_education)
            5. Add skills (save_skills)
            6. Add additional information (save_additional)
            7. Finalize the resume (finalize_resume)
            
            CONVERSATION STYLE:
            - Be conversational and friendly
            - Ask one question at a time
            - Confirm information before saving
            - Provide helpful suggestions and tips
            - Always acknowledge when information is saved successfully""",
            functions=functions
        )
        
        if assistant_id:
            logger.info(f"Resume Builder Assistant created with ID: {assistant_id}")
        else:
            logger.error("Failed to create Resume Builder Assistant")
    
    return assistant_manager, assistant_id

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def chat_with_ai(request):
    """
    Django view for handling AI chat with proper user management
    
    This view demonstrates how to:
    1. Ensure user is authenticated
    2. Pass user_id to the AI assistant
    3. Handle conversation threads per user
    4. Return responses to the frontend
    """
    try:
        # Get the authenticated user
        user = request.user
        user_id = str(user.id)
        
        # Parse the request
        data = json.loads(request.body)
        message = data.get('message', '')
        thread_id = data.get('thread_id')  # Frontend should manage thread IDs
        
        # Get or create assistant
        manager, assistant_id = get_or_create_assistant()
        
        if not assistant_id:
            return JsonResponse({
                'success': False,
                'error': 'Assistant not available'
            }, status=500)
        
        # Create thread if not provided
        if not thread_id:
            thread_id = manager.create_thread()
            if not thread_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to create conversation thread'
                }, status=500)
        
        # Send message to AI with user context
        response = manager.add_message_and_run(
            thread_id=thread_id,
            assistant_id=assistant_id,
            query=message,
            user_id=user_id
        )
        
        if response:
            return JsonResponse({
                'success': True,
                'response': response,
                'thread_id': thread_id,
                'user_id': user_id
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No response from assistant',
                'thread_id': thread_id
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in chat_with_ai: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@login_required
def get_user_resumes(request):
    """
    Django view to get all resumes for the authenticated user
    
    This demonstrates how the AI assistant can access user-specific data
    """
    try:
        user = request.user
        user_id = str(user.id)
        
        # Get or create assistant
        manager, assistant_id = get_or_create_assistant()
        
        if not assistant_id:
            return JsonResponse({
                'success': False,
                'error': 'Assistant not available'
            }, status=500)
        
        # Create a temporary thread for this operation
        thread_id = manager.create_thread()
        
        # Ask the AI to list user resumes
        response = manager.add_message_and_run(
            thread_id=thread_id,
            assistant_id=assistant_id,
            query="Please list all my resumes",
            user_id=user_id
        )
        
        return JsonResponse({
            'success': True,
            'response': response,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error in get_user_resumes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

# Example WebSocket consumer (for Django Channels)
class ResumeBuilderConsumer:
    """
    WebSocket consumer for real-time resume building
    
    This shows how to integrate with Django Channels for real-time chat
    """
    
    def __init__(self):
        self.manager, self.assistant_id = get_or_create_assistant()
    
    def connect(self, scope, user):
        """Handle WebSocket connection"""
        if user.is_authenticated:
            # Accept the connection
            self.accept()
            self.user_id = str(user.id)
            self.thread_id = self.manager.create_thread()
            
            # Send welcome message
            self.send(text_data=json.dumps({
                'type': 'welcome',
                'message': f'Welcome {user.username}! I\'m here to help you build your resume.',
                'thread_id': self.thread_id
            }))
        else:
            # Reject unauthenticated connections
            self.close()
    
    def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
            
            # Send message to AI with user context
            response = self.manager.add_message_and_run(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                query=message,
                user_id=self.user_id
            )
            
            # Send response back to client
            self.send(text_data=json.dumps({
                'type': 'ai_response',
                'message': response,
                'user_id': self.user_id
            }))
            
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {str(e)}")
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'An error occurred while processing your message.'
            }))

# Example usage in a Django template
"""
Frontend JavaScript example:

```javascript
// Connect to WebSocket
const socket = new WebSocket('ws://localhost:8000/ws/resume-builder/');

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'welcome') {
        console.log('Connected to AI assistant');
        console.log('Thread ID:', data.thread_id);
    } else if (data.type === 'ai_response') {
        // Display AI response in chat interface
        displayMessage(data.message, 'ai');
    }
};

// Send message to AI
function sendMessage(message) {
    socket.send(JSON.stringify({
        'message': message
    }));
}

// Example: Start resume creation
sendMessage("Hi! I want to create a new resume. Can you help me?");
```

Django URL configuration:

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/chat/', views.chat_with_ai, name='chat_with_ai'),
    path('api/resumes/', views.get_user_resumes, name='get_user_resumes'),
]
```

Django Channels routing:

```python
# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/resume-builder/$', consumers.ResumeBuilderConsumer.as_asgi()),
]
```
"""

# Example of how the AI assistant handles user context
"""
When a user sends a message like:
"I want to create a resume for Sarah Johnson"

The AI assistant will:

1. Call create_resume function with:
   {
     "user_id": "123",  // The authenticated user's ID
     "resume_name": "Sarah Johnson's Resume",
     "template_id": "professional"
   }

2. The function handler will:
   - Validate that user_id "123" exists in the database
   - Create a new resume associated with that user
   - Return the resume_id for future operations

3. For subsequent operations, the AI will include both user_id and resume_id:
   {
     "user_id": "123",
     "resume_id": "456",
     "full_name": "Sarah Johnson",
     "email": "sarah@example.com",
     ...
   }

4. The function handler will:
   - Validate the user owns the resume
   - Update only that specific resume
   - Return success/error with user context

This ensures:
- Data isolation between users
- Security (users can only access their own resumes)
- Proper audit trails
- Scalability for multi-user environments
""" 
 