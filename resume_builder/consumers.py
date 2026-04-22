"""
WebSocket consumers for resume_builder app.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Resume
from .template_registry import templates_for_gallery


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
        
        template_names = [t["name"] for t in templates_for_gallery()]
        welcome = (
            "Hello! I'm here to help you create a beautiful resume. "
            f"Available templates: {', '.join(template_names)}. "
            "Which style appeals to you?"
        )
        await self.send(text_data=json.dumps({
            'type': 'welcome_message',
            'message': welcome,
            'templates': template_names,
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
            resume_id = text_data_json.get('resume_id')  # Extract resume_id from message
            
            print(f"🔍 WebSocket received message: {message}")
            print(f"🔍 Message type: {message_type}")
            print(f"🔍 Thread ID: {thread_id}")
            print(f"🔍 .............................Resume ID..............................: {resume_id}")  # Debug print for resume_id
            
            # Process message through real AI assistant with resume_id
            response = await self.process_with_real_ai(message, thread_id, resume_id)
            
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
    def process_with_real_ai(self, message, thread_id, resume_id=None):
        """
        Process user message with the real AI assistant manager.
        This integrates with your OpenAI Assistant Manager.
        """
        try:
            print(f"🤖 Processing message with real AI: {message}")
            print(f"🤖 Resume ID provided: {resume_id}")  # Debug print
            
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
            
            # Smart resume data inclusion - now with explicit resume_id
            enhanced_message = self._prepare_message_with_smart_resume_context(message, resume_id)
            
            print(f"🤖 Sending message to AI assistant")
            print(f"📤 Thread ID: {thread_id}")
            print(f"📤 Assistant ID: {assistant_id}")
            print(f"📤 User ID: {self.user_id}")
            print(f"📤 Resume ID: {resume_id}")  # Debug print
            
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
                elif resume_id:  # Use the resume_id from the request if AI didn't return one
                    response_data['resume_id'] = resume_id
                
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
        return await self.process_with_real_ai(message, None, None)

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

    def _prepare_message_with_smart_resume_context(self, message, resume_id=None):
        """
        Prepare message with resume context if needed.
        Only includes resume data if a specific resume_id is provided.
        """
        from datetime import datetime  # Import datetime here since we use it
        
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
            'technology', 'software', 'tool', 'language', 'framework', 'platform',
            'cover letter', 'cover', 'letter', 'job application', 'apply', 'position'
        ]
        
        message_lower = message.lower()
        is_resume_related = any(keyword in message_lower for keyword in resume_keywords)
        
        print(f"🔍 Message analysis: '{message}'")
        print(f"🔍 Resume-related: {is_resume_related}")
        print(f"🔍 Resume ID provided: {resume_id}")
        
        # If not resume-related, just return the message
        if not is_resume_related:
            print(f"📄 No resume data needed for general chat")
            return message
        
        # Only proceed if a specific resume_id is provided
        if not resume_id:
            print(f"📄 No resume ID provided for resume-related operation")
            enhanced_message = f"""
User Request: {message}

IMPORTANT: This request requires working with a specific resume, but no resume has been selected.

Please do one of the following:
1. **Select a resume from your resume list** - Ask the user to view their resume list and select a specific resume to work with
2. **Create a new resume** - If they want to start fresh, guide them through creating a new resume
3. **Ask for clarification** - If they mentioned editing something but didn't specify which resume, ask them to clarify

DO NOT automatically assume which resume to use. Always ask the user to explicitly select or create a resume first.

Example responses:
- "I'd be happy to help you with that! First, let me show you your resume list so you can select which resume to work with."
- "To help you with that, I need to know which resume you'd like to work with. Would you like me to show you your resume list?"
- "I can help you edit your resume! Do you want to work with an existing resume, or would you like to create a new one?"
"""
            return enhanced_message
        
        # Try to get resume data using the provided resume_id
        current_resume = None
        print(f"📄 Looking for specific resume ID: {resume_id}")
        try:
            current_resume = Resume.objects.filter(
                user=self.user, 
                id=resume_id
            ).first()
            if current_resume:
                print(f"✅ Found resume with ID {resume_id}: {current_resume.name}")
            else:
                print(f"❌ Resume with ID {resume_id} not found for user {self.user.id}")
        except Exception as e:
            print(f"⚠️ Error looking up resume ID {resume_id}: {e}")
        
        # If we found a resume, include its data
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
            # Resume ID provided but not found
            print(f"📄 Resume ID {resume_id} not found - prompting user to select valid resume")
            enhanced_message = f"""
User Request: {message}

ERROR: The specified resume (ID: {resume_id}) was not found or is not accessible.

Please ask the user to:
1. **Select a different resume** from their resume list
2. **Create a new resume** if they want to start fresh
3. **Check their resume list** to see available resumes

DO NOT proceed with the operation until a valid resume is selected.

Example response:
"I couldn't find the resume you're trying to work with. Let me show you your available resumes so you can select the correct one, or we can create a new resume if you prefer."
"""
            return enhanced_message 