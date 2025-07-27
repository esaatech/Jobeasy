"""
Interview Coach Manager

This module provides a complete interface for managing interview coaching
using OpenAI Assistants with user-specific threads for conversation memory.
"""

from django.conf import settings
from .ai_resume_assistant import OpenAIAssistantManager
from question_answer.models import InterviewAssistant
import os


class InterviewCoachManager:
    """
    Manages interview coaching using OpenAI Assistants
    
    This class provides a complete interface for interview coaching with:
    - Shared assistant for all users (cost-effective)
    - User-specific threads for conversation memory
    - Personalized coaching based on question context
    
    WORKFLOW:
    1. User requests coaching for a specific question
    2. Get or create user's thread
    3. Send question context + user message to shared assistant
    4. Return personalized coaching response
    
    USAGE:
        coach_manager = InterviewCoachManager()
        response = coach_manager.get_coaching_response(
            user=request.user,
            question_context="Question: Tell me about yourself...",
            user_message="How should I structure my answer?"
        )
    """
    
    def __init__(self):
        """Initialize the Interview Coach Manager"""
        self.assistant_manager = OpenAIAssistantManager()
        
        # Get assistant ID from environment variable (optional during setup)
        self.assistant_id = os.getenv('INTERVIEW_COACH_ASSISTANT_ID')
    
    def get_or_create_user_thread(self, user):
        """
        Get existing thread or create new one for user
        
        Args:
            user: Django User object
            
        Returns:
            str: Thread ID for the user
        """
        interview_assistant, created = InterviewAssistant.objects.get_or_create(user=user)
        
        if not interview_assistant.interview_thread_id:
            thread_id = self.assistant_manager.create_thread()
            interview_assistant.interview_thread_id = thread_id
            interview_assistant.save()
        
        return interview_assistant.interview_thread_id
    
    def get_coaching_response(self, user, question_context, user_message):
        """
        Get personalized coaching response for user
        
        Args:
            user: Django User object
            question_context (str): Context about the interview question
            user_message (str): User's specific question/request
            
        Returns:
            dict: Response from AI assistant with coaching advice
        """
        # Check if assistant ID is available
        if not self.assistant_id:
            raise ValueError(
                "INTERVIEW_COACH_ASSISTANT_ID not found in environment variables. "
                "Please run 'python manage.py setup_interview_coach' first."
            )
        
        # Get or create user's thread
        thread_id = self.get_or_create_user_thread(user)
        
        # Build comprehensive context
        full_context = f"""
        INTERVIEW QUESTION CONTEXT:
        {question_context}
        
        USER'S QUESTION:
        {user_message}
        
        As an expert interview coach, provide personalized guidance on:
        1. How to approach this specific question
        2. Key points to include in the answer
        3. Common mistakes to avoid
        4. Follow-up questions they might ask
        5. Practice strategies for this type of question
        
        IMPORTANT: Format your response using markdown for better readability:
        - Use ### for main sections
        - Use **bold** for emphasis
        - Use bullet points (- or *) for lists
        - Use numbered lists (1., 2., 3.) for steps
        - Keep paragraphs concise and well-structured
        
        Be encouraging, constructive, and specific to the question context provided.
        """
        
        # Get response from OpenAI Assistant
        result = self.assistant_manager.add_message_and_run(
            thread_id=thread_id,
            assistant_id=self.assistant_id,
            query=full_context,
            user_id=user.id
        )
        
        return result
    
    def create_interview_assistant(self):
        """
        Create the shared interview coach assistant
        
        This method should be run once during setup to create the assistant
        that will be shared across all users.
        
        Returns:
            str: Assistant ID if successful, None if failed
        """
        try:
            assistant_id = self.assistant_manager.create_assistant(
                name="Interview Coach",
                base_instructions="""You are an expert interview coach with deep knowledge of various interview types and techniques. Your role is to:

1. ANALYZE INTERVIEW QUESTIONS: Understand the context, category, and requirements of each question
2. PROVIDE STRUCTURED GUIDANCE: Help users understand how to approach different types of questions
3. GIVE SPECIFIC FEEDBACK: Provide actionable tips and examples for improvement
4. SUGGEST PRACTICE STRATEGIES: Recommend ways to practice and prepare for similar questions
5. IDENTIFY COMMON MISTAKES: Point out typical errors and how to avoid them
6. ENCOURAGE CONFIDENCE: Be supportive and constructive in your feedback

INTERVIEW CATEGORIES YOU SPECIALIZE IN:
- General/Behavioral Questions
- Technical Questions
- System Design Questions
- Leadership/Management Questions
- Problem-Solving Questions
- Crisis Management Questions

RESPONSE STRUCTURE:
- Start with a brief analysis of the question type
- Provide specific guidance tailored to the question
- Include concrete examples when helpful
- Suggest follow-up questions they might encounter
- End with encouragement and next steps

Always be encouraging, constructive, and focus on the specific question context provided.""",
                functions=[],
                model="gpt-4o-mini"
            )
            
            print(f"Interview Coach Assistant created with ID: {assistant_id}")
            print("Add this ID to your environment variables:")
            print(f"INTERVIEW_COACH_ASSISTANT_ID={assistant_id}")
            
            return assistant_id
            
        except Exception as e:
            print(f"Error creating interview assistant: {e}")
            return None
    
    def get_user_conversation_history(self, user, limit=5):
        """
        Get user's recent conversation history (for future enhancement)
        
        Args:
            user: Django User object
            limit (int): Number of recent messages to retrieve
            
        Returns:
            list: Recent conversation messages
        """
        # This is a placeholder for future enhancement
        # Could be used to provide more personalized coaching
        return []
    
    def reset_user_thread(self, user):
        """
        Reset user's conversation thread (start fresh)
        
        Args:
            user: Django User object
            
        Returns:
            bool: True if successful, False if failed
        """
        try:
            interview_assistant = InterviewAssistant.objects.get(user=user)
            
            # Create new thread
            new_thread_id = self.assistant_manager.create_thread()
            
            # Update user's thread ID
            interview_assistant.interview_thread_id = new_thread_id
            interview_assistant.save()
            
            return True
            
        except Exception as e:
            print(f"Error resetting user thread: {e}")
            return False 