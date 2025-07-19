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
            thread_id = text_data_json.get('thread_id')
            
            print(f"🔍 WebSocket received message: {message}")
            print(f"🔍 Message type: {message_type}")
            print(f"🔍 Thread ID: {thread_id}")
            
            # Process message through real AI assistant
            response = await self.process_with_real_ai(message, thread_id)
            
            # Send response back to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'message': response['message'],
                'action': response.get('action'),
                'data': response.get('data'),
                'thread_id': response.get('thread_id'),
                'resume_id': response.get('resume_id')
            }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            print(f"❌ WebSocket error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'An error occurred: {str(e)}'
            }))

    @database_sync_to_async
    def process_with_real_ai(self, message, thread_id):
        """
        Process user message with the real AI assistant manager.
        This integrates with your OpenAI Assistant Manager.
        """
        try:
            print(f"🤖 Processing message with real AI: {message}")
            
            # Import the AI assistant manager
            from resume_builder.views import get_or_create_assistant
            
            # Get or create assistant
            manager, assistant_id = get_or_create_assistant()
            
            if not assistant_id:
                print("❌ No assistant available")
                return {
                    'message': "I'm sorry, I'm having trouble connecting to my AI assistant right now. Please try again later.",
                    'thread_id': thread_id
                }
            
            # Create thread if not provided
            if not thread_id:
                print("🧵 Creating new thread")
                thread_id = manager.create_thread()
                if not thread_id:
                    return {
                        'message': "I'm sorry, I couldn't create a conversation thread. Please try again.",
                        'thread_id': None
                    }
            
            print(f"🤖 Sending message to AI assistant")
            print(f"📤 Thread ID: {thread_id}")
            print(f"📤 Assistant ID: {assistant_id}")
            print(f"📤 User ID: {self.user_id}")
            
            # Send message to AI with user context
            result = manager.add_message_and_run(
                thread_id=thread_id,
                assistant_id=assistant_id,
                query=message,
                user_id=self.user_id
            )
            
            print(f"📥 AI result: {result}")
            
            if result:
                response_data = {
                    'message': result['response'],
                    'thread_id': thread_id,
                    'user_id': self.user_id
                }
                
                # Add resume ID if available
                if result.get('resume_id'):
                    response_data['resume_id'] = result['resume_id']
                
                return response_data
            else:
                return {
                    'message': "I'm sorry, I didn't get a response from my AI assistant. Please try again.",
                    'thread_id': thread_id
                }
                
        except Exception as e:
            print(f"❌ Error in process_with_real_ai: {str(e)}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
            return {
                'message': f"I'm sorry, I encountered an error: {str(e)}",
                'thread_id': thread_id
            }

    async def process_with_ai(self, message, message_type):
        """
        DEPRECATED: This method is no longer used.
        Kept for backward compatibility.
        """
        # This method is deprecated - use process_with_real_ai instead
        return await self.process_with_real_ai(message, None)

    async def send_event(self, event):
        """
        Send events from function handlers to the frontend.
        This is called by the EventEmitter when function handlers want to trigger frontend actions.
        """
        await self.send(text_data=json.dumps({
            'type': 'backend_event',
            'event_type': event['event_type'],
            'data': event['data']
        }))

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