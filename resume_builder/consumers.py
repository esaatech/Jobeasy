"""
WebSocket consumers for resume_builder app.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Resume


class ResumeBuilderConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for resume builder chat interface.
    Handles real-time communication between users and AI assistant.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Get user from scope
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        self.user_id = str(self.user.id)
        self.room_group_name = f'resume_builder_{self.user_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'welcome_message',
            'message': 'Hello! I\'m here to help you create a beautiful resume. I have several templates available: [Professional] [Modern] [Creative] [Minimal]. Which style appeals to you?',
            'templates': ['Professional', 'Modern', 'Creative', 'Minimal']
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            message_type = text_data_json.get('type', 'user_message')
            
            # Process message through AI assistant
            response = await self.process_with_ai(message, message_type)
            
            # Send response back to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'message': response['message'],
                'action': response.get('action'),
                'data': response.get('data')
            }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'An error occurred: {str(e)}'
            }))

    async def process_with_ai(self, message, message_type):
        """
        Process user message with AI assistant.
        This will integrate with your OpenAI Assistant Manager later.
        """
        # For now, return a simple response
        # Later, this will call your AI service
        
        if message_type == 'template_selection':
            return {
                'message': f'Great choice! I\'ve selected the {message} template. Let\'s start with your personal information. What\'s your full name?',
                'action': 'template_selected',
                'data': {'template': message}
            }
        elif 'name' in message.lower():
            return {
                'message': f'Nice to meet you! I\'ve added your name. Now, what\'s your professional title?',
                'action': 'personal_info_updated',
                'data': {'field': 'name', 'value': message}
            }
        elif 'title' in message.lower() or 'engineer' in message.lower() or 'manager' in message.lower():
            return {
                'message': f'Excellent! I\'ve added your title. Next, what\'s your email address?',
                'action': 'personal_info_updated',
                'data': {'field': 'title', 'value': message}
            }
        else:
            return {
                'message': f'I understand you said: "{message}". Let me help you with that. What specific information would you like to add to your resume?',
                'action': 'general_response'
            }

    async def resume_updated(self, event):
        """Send resume update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'resume_updated',
            'resume_data': event['resume_data'],
            'progress': event['progress']
        }))

    async def section_completed(self, event):
        """Send section completion notification."""
        await self.send(text_data=json.dumps({
            'type': 'section_completed',
            'section': event['section'],
            'next_section': event['next_section']
        }))

    async def template_changed(self, event):
        """Send template change notification."""
        await self.send(text_data=json.dumps({
            'type': 'template_changed',
            'template_id': event['template_id']
        })) 