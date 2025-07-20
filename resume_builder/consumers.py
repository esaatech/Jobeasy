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
            from datetime import datetime
            import json
            
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
            
            # Smart resume data inclusion - only include if we have a recent resume from AI interaction
            enhanced_message = self._prepare_message_with_smart_resume_context(message)
            
            print(f"🤖 Sending message to AI assistant")
            print(f"📤 Thread ID: {thread_id}")
            print(f"📤 Assistant ID: {assistant_id}")
            print(f"📤 User ID: {self.user_id}")
            
            # Send message to AI with user context
            result = manager.add_message_and_run(
                thread_id=thread_id,
                assistant_id=assistant_id,
                query=enhanced_message,
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

    def _prepare_message_with_smart_resume_context(self, message):
        """
        Smart function to determine when resume data is needed and include it only when necessary.
        This reduces token usage by not sending full resume data for general chat.
        """
        # Keywords that indicate resume-related operations
        resume_keywords = [
            'resume', 'cv', 'curriculum vitae', 'create resume', 'build resume', 'edit resume',
            'update', 'change', 'modify', 'delete', 'remove', 'add', 'edit', 'save',
            'experience', 'education', 'skills', 'personal', 'summary', 'template',
            'university', 'college', 'school', 'degree', 'company', 'job', 'work',
            'position', 'title', 'employment', 'career', 'professional', 'work history',
            'academic', 'qualification', 'certification', 'training', 'course',
            'skill', 'competency', 'expertise', 'proficiency', 'knowledge',
            'project', 'achievement', 'accomplishment', 'responsibility', 'duty',
            'technology', 'software', 'tool', 'language', 'framework', 'platform'
        ]
        
        # Check if message contains resume-related keywords
        message_lower = message.lower()
        is_resume_related = any(keyword in message_lower for keyword in resume_keywords)
        
        print(f"🔍 Message analysis: '{message}'")
        print(f"🔍 Resume-related: {is_resume_related}")
        
        # CRITICAL: Only include resume data if we have a resume_id from previous AI interaction
        # This means the AI has already created a resume in this conversation
        if not is_resume_related:
            # For general chat, just send the message without resume data
            print(f"📄 No resume data needed for general chat")
            return message
        
        # For resume-related operations, check if we have a resume_id from previous AI interaction
        # We'll need to check the thread history or store resume_id in session/context
        # For now, let's check if there's a recent resume created by this user
        try:
            # Get user's most recent resume that was created recently (within last 10 minutes)
            from django.utils import timezone
            from datetime import timedelta
            
            recent_time = timezone.now() - timedelta(minutes=10)
            current_resume = Resume.objects.filter(
                user=self.user, 
                created_at__gte=recent_time
            ).order_by('-created_at').first()
            
            if current_resume:
                # Prepare resume data for AI context
                resume_data = {
                    'resume_id': str(current_resume.id),
                    'name': current_resume.name,
                    'template_id': current_resume.template_id,
                    'personal_info': current_resume.personal_info or {},
                    'experience': current_resume.experience or [],
                    'education': current_resume.education or [],
                    'skills': current_resume.skills or {},
                    'additional': current_resume.additional or {},
                    'draft': current_resume.draft,
                    'updated_at': current_resume.updated_at.isoformat() if current_resume.updated_at else None
                }
                
                # Include resume data in user message
                enhanced_message = f"""
Current Resume State (as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):
{json.dumps(resume_data, indent=2)}

User Request: {message}

Note: You can edit and delete entries using their array indices (0, 1, 2, etc.). The resume data above shows the current state.

CRITICAL: When editing or deleting entries, you MUST search through the current resume data provided above to find the correct entry. Do NOT rely on conversation history or previous entries - always use the current data shown above to determine the correct index.

SEARCH PROCESS FOR EDITING/DELETING:
1. First, identify what the user wants to edit/delete (institution name, company name, etc.)
2. Search through the current education/experience arrays in the resume data above
3. Look for EXACT or PARTIAL matches in the relevant fields
4. Use the ARRAY INDEX (0, 1, 2, etc.) of the matching entry
5. If multiple entries match, ask the user to be more specific
6. If no entry matches, inform the user that the specified entry was not found

EXAMPLE SEARCH PROCESS:
- User says: "update tech university to techno"
- Search education array for "tech university" in institution field
- Find entry at index 1 with institution "Tech University"
- Call edit_education with education_index=1, field="institution", value="Techno University"

CRITICAL: Before calling edit_education or delete_education, you MUST:
1. State which entry you found (e.g., "I found Tech University at index 1")
2. Confirm the action you're taking (e.g., "I will update Tech University to Techno University")
3. Then call the function with the correct index
"""
                print(f"📄 Resume data included for AI context")
                print(f"📄 Resume ID: {resume_data['resume_id']}")
                print(f"📄 Education entries: {len(resume_data['education'])}")
                print(f"📄 Experience entries: {len(resume_data['experience'])}")
                
                # Debug: Show education entries with indices
                print(f"\n🔍 DEBUG: Current Education Entries:")
                for i, edu in enumerate(resume_data['education']):
                    print(f"  Index {i}: {edu.get('degree', 'N/A')} from {edu.get('institution', 'N/A')}")
                print(f"🔍 DEBUG: End Education Entries\n")
                
                return enhanced_message
            else:
                # No recent resume found - this is likely a new conversation
                print(f"📄 No recent resume found - treating as new conversation")
                return message
        except Exception as e:
            print(f"⚠️ Error getting resume data: {e}")
            return message 