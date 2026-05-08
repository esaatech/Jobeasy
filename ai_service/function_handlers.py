from typing import Dict, Any, List
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import json

from resume_builder.template_registry import get_valid_template_ids

logger = logging.getLogger(__name__)


class EventEmitter:
    """Handles sending events to frontend via Django Channels"""
    
    @staticmethod
    def emit_event(user_id: str, event_type: str, data: Dict[str, Any]):
        """
        Emit an event to the frontend via Django Channels
        
        Args:
            user_id: ID of the user to send event to
            event_type: Type of event (e.g., 'template_changed', 'resume_updated')
            data: Event data to send
        """
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            group_name = f'resume_builder_{user_id}'
            
            # Send event to the user's WebSocket group
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_event',
                    'event_type': event_type,
                    'data': data
                }
            )
            
            print(f"🎯 Event emitted: {event_type} to user {user_id}")
            print(f"📤 Event data: {data}")
            
        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {str(e)}")
            print(f"❌ Event emission failed: {str(e)}")

class FunctionHandlers:
    """Implements the actual functions that the AI can call for resume building"""
    
    def __init__(self, user_id: str = None):
        """
        Initialize function handlers with user context
        
        Args:
            user_id: ID of the user creating the resume (required for all operations)
        """
        self.user_id = user_id
        self._setup_django()
    
    def _setup_django(self):
        """Setup Django environment for database operations"""
        try:
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
                
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            self.Resume = Resume
            self.User = User
            
        except Exception as e:
            logger.error(f"Failed to setup Django: {str(e)}")
            raise
    
    @staticmethod
    def _convert_to_int(value: str, field_name: str) -> int:
        """Convert string ID to integer with proper error handling"""
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid {field_name} format: {value}. Must be a number.")
    
    def _get_user(self):
        """Get the current user by user_id"""
        if not self.user_id:
            raise ValueError("user_id is required for all operations")
        
        try:
            numeric_user_id = self._convert_to_int(self.user_id, "user_id")
            user = self.User.objects.get(id=numeric_user_id)
            return user
        except self.User.DoesNotExist:
            raise ValueError(f"User with ID {self.user_id} not found")
        except Exception as e:
            logger.error(f"Error getting user {self.user_id}: {str(e)}")
            raise
    
    def _get_resume(self, resume_id: str):
        """Get a specific resume by ID for the current user"""
        try:
            user = self._get_user()
            numeric_resume_id = self._convert_to_int(resume_id, "resume_id")
            resume = self.Resume.objects.get(id=numeric_resume_id, user=user)
            return resume
        except self.Resume.DoesNotExist:
            raise ValueError(f"Resume with ID {resume_id} not found for user {self.user_id}")
        except Exception as e:
            logger.error(f"Error getting resume {resume_id} for user {self.user_id}: {str(e)}")
            raise

    @staticmethod
    def create_resume(user_id: str, resume_name: str, template_id: str = "professional") -> Dict[str, Any]:
        """Create a new resume for the specified user"""
        try:
            print(f"\n========== CREATE RESUME ==========")
            print(f"User ID: {user_id}")
            print(f"Resume Name: {resume_name}")
            print(f"Template ID: {template_id}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Convert user_id to integer using helper method
            try:
                numeric_user_id = FunctionHandlers._convert_to_int(user_id, "user_id")
            except ValueError as e:
                return {"success": False, "error": str(e)}
            
            # Validate user exists
            try:
                user = User.objects.get(id=numeric_user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Create new resume
            resume = Resume.objects.create(
                user=user,
                name=resume_name,
                draft=True,
                template_id=template_id,
                personal_info={},
                experience=[],
                education=[],
                skills={},
                additional={}
            )
            
            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_created', {
                'resume_id': str(resume.id),
                'resume_name': resume_name,
                'template_id': template_id,
                'status': 'draft'
            })
            
            result = {
                "success": True,
                "message": f"## ✅ Resume Created Successfully!\n\n**Resume Name:** {resume_name}\n**Template:** {template_id}\n**Status:** Draft\n\nI've created your resume and I'm ready to guide you through each section step by step. Let's start with your **personal information**!\n\n**What I need from you:**\n• Full name\n• Email address\n• Phone number\n• Location (City, State/Country)\n• Professional title",
                "data": {
                    "resume_id": str(resume.id),
                    "user_id": str(user.id),
                    "username": user.username,
                    "resume_name": resume_name,
                    "template_id": template_id,
                    "status": "draft",
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in create_resume: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def save_personal_info(
        user_id: str,
        resume_id: str,
        full_name: str,
        email: str,
        phone: str = None,
        location: str = None,
        linkedin: str = None,
        title: str = None
    ) -> Dict[str, Any]:
        """Save personal information for resume with comprehensive validation (summary will be generated later)"""
        try:
            print(f"\n========== SAVE PERSONAL INFO ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Full Name: {full_name}")
            print(f"Email: {email}")
            print(f"Phone: {phone}")
            print(f"Location: {location}")
            print(f"LinkedIn: {linkedin}")
            print(f"Title: {title}")
            
            # Validation: Check required fields
            validation_errors = []
            
            if not full_name or not full_name.strip():
                validation_errors.append("Full name is required")
            
            if not email or not email.strip():
                validation_errors.append("Email is required")
            elif not FunctionHandlers._is_valid_email(email):
                validation_errors.append("Please provide a valid email address")
            
            if not phone or not phone.strip():
                validation_errors.append("Phone number is required")
            
            if not location or not location.strip():
                validation_errors.append("Location is required")
            
            if not title or not title.strip():
                validation_errors.append("Professional title is required")
            
            if validation_errors:
                return {
                    "success": False,
                    "error": "Please provide the following information: " + ", ".join(validation_errors),
                    "missing_fields": validation_errors,
                    "action": "request_missing_info"
                }
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Update personal info (summary will be added later)
            resume.personal_info = {
                'full_name': full_name.strip(),
                'email': email.strip(),
                'phone': phone.strip() if phone else '',
                'location': location.strip() if location else '',
                'linkedin': linkedin.strip() if linkedin else '',
                'title': title.strip() if title else '',
                'summary': ''  # Will be populated later by save_summary function
            }
            
            # Update resume name if it's generic
            if resume.name in ["My Resume", "New Resume"]:
                resume.name = f"{full_name.strip()}'s Resume"
            
            resume.save()
            
            # Emit events to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'personal_info': resume.personal_info,
                'timestamp': datetime.now().isoformat()
            })
            
            EventEmitter.emit_event(user_id, 'section_completed', {
                'section': 'personal_info',
                'data': resume.personal_info,
                'next_section': 'experience',
                'timestamp': datetime.now().isoformat()
            })

            result = {
                "success": True,
                "message": f"## ✅ Personal Information Saved!\n\n**Name:** {full_name}\n**Email:** {email}\n**Phone:** {phone}\n**Location:** {location}\n**Title:** {title}\n\nPerfect! I've captured your contact details and professional title. Now let's move on to your **work experience**.\n\n**What I need from you:**\n• Job title\n• Company name\n• Start and end dates\n• Job description and achievements\n\nYou can add multiple jobs, and I'll help you format them properly!",
                "data": {
                    "resume_id": str(resume.id),
                    "user_id": str(user.id),
                    "username": user.username,
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "location": location,
                    "linkedin": linkedin,
                    "title": title,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in save_personal_info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Simple email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def save_experience(
        user_id: str,
        resume_id: str,
        experience_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Save work experience with comprehensive validation"""
        try:
            print(f"\n========== SAVE EXPERIENCE ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Experience entries: {len(experience_entries)}")
            
            # Debug: Print each experience entry
            for i, entry in enumerate(experience_entries):
                print(f"\n--- Experience Entry {i+1} ---")
                print(f"Title: {entry.get('title', 'NOT PROVIDED')}")
                print(f"Company: {entry.get('company', 'NOT PROVIDED')}")
                print(f"Start Date: {entry.get('start_date', 'NOT PROVIDED')}")
                print(f"End Date: {entry.get('end_date', 'NOT PROVIDED')}")
                print(f"Current: {entry.get('current', 'NOT PROVIDED')}")
                print(f"Description: {entry.get('description', 'NOT PROVIDED')[:100]}...")
            
            # Validation: Check if experience entries are provided
            if not experience_entries or len(experience_entries) == 0:
                return {
                    "success": False,
                    "error": "Please provide at least one work experience entry",
                    "action": "request_experience_info"
                }
            
            # Validate each experience entry
            validation_errors = []
            for i, entry in enumerate(experience_entries):
                entry_errors = []
                
                if not entry.get('title') or not entry['title'].strip():
                    entry_errors.append("job title")
                
                if not entry.get('company') or not entry['company'].strip():
                    entry_errors.append("company name")
                
                if not entry.get('start_date'):
                    entry_errors.append("start date")
                
                if not entry.get('end_date'):
                    entry_errors.append("end date")
                
                if not entry.get('description') or not entry['description'].strip():
                    entry_errors.append("job description")
                
                if entry_errors:
                    validation_errors.append(f"Entry {i+1}: missing {', '.join(entry_errors)}")
            
            if validation_errors:
                return {
                    "success": False,
                    "error": "Please complete the following information: " + "; ".join(validation_errors),
                    "missing_fields": validation_errors,
                    "action": "request_missing_info"
                }
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Clean and validate experience data
            cleaned_experience = []
            for entry in experience_entries:
                cleaned_entry = {
                    'title': entry['title'].strip(),
                    'company': entry['company'].strip(),
                    'start_date': entry['start_date'],
                    'end_date': entry.get('end_date', 'Present'),
                    'description': entry['description'].strip()
                }
                cleaned_experience.append(cleaned_entry)
            
            # Debug: Print cleaned experience data
            print(f"\n--- CLEANED EXPERIENCE DATA ---")
            for i, entry in enumerate(cleaned_experience):
                print(f"Entry {i+1}: {entry}")
            
            # Update resume - preserve existing data and only update experience
            existing_personal_info = resume.personal_info or {}
            existing_education = resume.education or []
            existing_skills = resume.skills or {}
            existing_additional = resume.additional or {}
            
            # Get existing experience and append new entries
            existing_experience = resume.experience or []
            print(f"\n--- EXISTING EXPERIENCE COUNT: {len(existing_experience)} ---")
            if existing_experience:
                print("Existing experience entries:")
                for i, entry in enumerate(existing_experience):
                    print(f"  {i+1}. {entry.get('title', 'N/A')} at {entry.get('company', 'N/A')}")
            
            # Append new experience entries to existing ones
            combined_experience = existing_experience + cleaned_experience
            print(f"\n--- COMBINED EXPERIENCE COUNT: {len(combined_experience)} ---")
            print(f"Added {len(cleaned_experience)} new entries to {len(existing_experience)} existing entries")
            
            # Update the experience section with combined data
            resume.experience = combined_experience
            
            # Preserve all other sections
            resume.personal_info = existing_personal_info
            resume.education = existing_education
            resume.skills = existing_skills
            resume.additional = existing_additional
            
            resume.save()
            
            # Emit events to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'experience': combined_experience,
                'timestamp': datetime.now().isoformat()
            })
            
            EventEmitter.emit_event(user_id, 'section_completed', {
                'section': 'experience',
                'data': combined_experience,
                'next_section': 'education',
                'timestamp': datetime.now().isoformat()
            })

            result = {
                "success": True,
                "message": f"## ✅ Work Experience Updated!\n\n**Total Experience Entries:** {len(combined_experience)}\n**New Entries Added:** {len(cleaned_experience)}\n\nGreat! I've saved your work experience. Now let's add your **education background**.\n\n**What I need from you:**\n• Degree or qualification\n• Institution name\n• Start and end dates\n• Any additional details (GPA, honors, etc.)\n\nYou can add multiple education entries, and I'll help you format them properly!",
                "data": {
                    "resume_id": str(resume.id),
                    "user_id": str(user.id),
                    "username": user.username,
                    "experience_count": len(combined_experience),
                    "experience": combined_experience,
                    "new_entries_added": len(cleaned_experience),
                    "existing_entries": len(existing_experience),
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in save_experience: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def edit_personal_info(user_id: str, resume_id: str, field: str, value: str) -> Dict[str, Any]:
        """Edit specific personal information field"""
        try:
            print(f"\n========== EDIT PERSONAL INFO ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Field: {field}")
            print(f"Value: {value}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Validate field
            valid_fields = ['full_name', 'email', 'phone', 'location', 'title']
            if field not in valid_fields:
                return {"success": False, "error": f"Invalid field. Must be one of: {', '.join(valid_fields)}"}
            
            # Update the specific field
            personal_info = resume.personal_info or {}
            personal_info[field] = value
            resume.personal_info = personal_info
            
            # Update resume name if full_name was changed
            if field == 'full_name' and resume.name in ["My Resume", "New Resume"]:
                resume.name = f"{value}'s Resume"
            
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'personal_info': resume.personal_info,
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Updated {field} to: {value}",
                "data": {
                    "resume_id": str(resume.id),
                    "field": field,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in edit_personal_info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def save_education(
        user_id: str,
        resume_id: str,
        education_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Save education with comprehensive validation"""
        try:
            print(f"\n========== SAVE EDUCATION ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Education entries: {len(education_entries)}")
            
            # Validation: Check if education entries are provided
            if not education_entries or len(education_entries) == 0:
                return {
                    "success": False,
                    "error": "Please provide at least one education entry",
                    "action": "request_education_info"
                }
            
            # Validate each education entry
            validation_errors = []
            for i, entry in enumerate(education_entries):
                entry_errors = []
                
                if not entry.get('degree') or not entry['degree'].strip():
                    entry_errors.append("degree")
                
                if not entry.get('institution') or not entry['institution'].strip():
                    entry_errors.append("institution name")
                
                if not entry.get('start_date'):
                    entry_errors.append("start date")
                
                if not entry.get('end_date'):
                    entry_errors.append("end date")
                
                if entry_errors:
                    validation_errors.append(f"Entry {i+1}: missing {', '.join(entry_errors)}")
            
            if validation_errors:
                return {
                    "success": False,
                    "error": "Please complete the following information: " + "; ".join(validation_errors),
                    "missing_fields": validation_errors,
                    "action": "request_missing_info"
                }
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Clean and validate education data
            cleaned_education = []
            for entry in education_entries:
                cleaned_entry = {
                    'degree': entry['degree'].strip(),
                    'institution': entry['institution'].strip(),
                    'start_date': entry['start_date'],
                    'end_date': entry.get('end_date', 'Present'),
                    'description': entry.get('description', '').strip()
                }
                cleaned_education.append(cleaned_entry)
            
            # Update resume - preserve existing data and only update education
            existing_personal_info = resume.personal_info or {}
            existing_experience = resume.experience or []
            existing_skills = resume.skills or {}
            existing_additional = resume.additional or {}
            
            # Get existing education and append new entries
            existing_education = resume.education or []
            print(f"\n--- EXISTING EDUCATION COUNT: {len(existing_education)} ---")
            if existing_education:
                print("Existing education entries:")
                for i, entry in enumerate(existing_education):
                    print(f"  {i+1}. {entry.get('degree', 'N/A')} from {entry.get('institution', 'N/A')}")
            
            # Append new education entries to existing ones
            combined_education = existing_education + cleaned_education
            print(f"\n--- COMBINED EDUCATION COUNT: {len(combined_education)} ---")
            print(f"Added {len(cleaned_education)} new entries to {len(existing_education)} existing entries")
            
            # Update the education section with combined data
            resume.education = combined_education
            
            # Preserve all other sections
            resume.personal_info = existing_personal_info
            resume.experience = existing_experience
            resume.skills = existing_skills
            resume.additional = existing_additional
            
            resume.save()
            
            # Emit events to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'education': combined_education,
                'timestamp': datetime.now().isoformat()
            })
            
            EventEmitter.emit_event(user_id, 'section_completed', {
                'section': 'education',
                'data': combined_education,
                'next_section': 'skills',
                'timestamp': datetime.now().isoformat()
            })

            result = {
                "success": True,
                "message": f"## ✅ Education Updated!\n\n**Total Education Entries:** {len(combined_education)}\n**New Entries Added:** {len(cleaned_education)}\n\nExcellent! I've saved your education background. Now let's add your **skills**.\n\n**What I need from you:**\n• **Technical Skills:** Programming languages, tools, technologies (e.g., Java, Python, React, AWS)\n• **Soft Skills:** Communication, teamwork, leadership, etc.\n• **Languages:** Spoken languages (e.g., English, Spanish, French)\n\nYou can provide skills in any category, and I'll organize them properly!",
                "data": {
                    "resume_id": str(resume.id),
                    "user_id": str(user.id),
                    "username": user.username,
                    "education_count": len(combined_education),
                    "education": combined_education,
                    "new_entries_added": len(cleaned_education),
                    "existing_entries": len(existing_education),
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in save_education: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def edit_education(user_id: str, resume_id: str, education_index: int, field: str, value: str) -> Dict[str, Any]:
        """Edit a specific education entry"""
        try:
            print(f"\n========== EDIT EDUCATION ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Education Index: {education_index}")
            print(f"Field: {field}")
            print(f"Value: {value}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Validate field
            valid_fields = ['degree', 'institution', 'start_date', 'end_date', 'gpa', 'description']
            if field not in valid_fields:
                return {"success": False, "error": f"Invalid field. Must be one of: {', '.join(valid_fields)}"}
            
            # Get current education
            current_education = resume.education or []
            if education_index >= len(current_education):
                return {"success": False, "error": f"Education index {education_index} out of range"}
            
            # Update the specific field
            current_education[education_index][field] = value
            resume.education = current_education
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'education': resume.education,
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Updated education {education_index} {field} to: {value}",
                "data": {
                    "resume_id": str(resume.id),
                    "education_index": education_index,
                    "field": field,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in edit_education: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def delete_education(user_id: str, resume_id: str, education_index: int) -> Dict[str, Any]:
        """Delete a specific education entry"""
        try:
            print(f"\n========== DELETE EDUCATION ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Education Index: {education_index}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Get current education
            current_education = resume.education or []
            if education_index >= len(current_education):
                return {"success": False, "error": f"Education index {education_index} out of range"}
            
            # Get the education entry to be deleted for the message
            deleted_education = current_education[education_index]
            
            # Remove the education entry
            current_education.pop(education_index)
            resume.education = current_education
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'education': resume.education,
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Deleted education: {deleted_education.get('degree', 'Unknown')} from {deleted_education.get('institution', 'Unknown')}",
                "data": {
                    "resume_id": str(resume.id),
                    "education_index": education_index,
                    "deleted_education": deleted_education,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in delete_education: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def edit_experience(user_id: str, resume_id: str, experience_index: int, field: str, value: str) -> Dict[str, Any]:
        """Edit a specific experience entry"""
        try:
            print(f"\n========== EDIT EXPERIENCE ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Experience Index: {experience_index}")
            print(f"Field: {field}")
            print(f"Value: {value}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Validate field
            valid_fields = ['title', 'company', 'start_date', 'end_date', 'description']
            if field not in valid_fields:
                return {"success": False, "error": f"Invalid field. Must be one of: {', '.join(valid_fields)}"}
            
            # Get current experience
            current_experience = resume.experience or []
            if experience_index >= len(current_experience):
                return {"success": False, "error": f"Experience index {experience_index} out of range"}
            
            # Update the specific field
            current_experience[experience_index][field] = value
            resume.experience = current_experience
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'experience': resume.experience,
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Updated experience {experience_index} {field} to: {value}",
                "data": {
                    "resume_id": str(resume.id),
                    "experience_index": experience_index,
                    "field": field,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in edit_experience: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def delete_experience(user_id: str, resume_id: str, experience_index: int) -> Dict[str, Any]:
        """Delete a specific experience entry"""
        try:
            print(f"\n========== DELETE EXPERIENCE ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Experience Index: {experience_index}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Get current experience
            current_experience = resume.experience or []
            if experience_index >= len(current_experience):
                return {"success": False, "error": f"Experience index {experience_index} out of range"}
            
            # Get the experience entry to be deleted for the message
            deleted_experience = current_experience[experience_index]
            
            # Remove the experience entry
            current_experience.pop(experience_index)
            resume.experience = current_experience
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'experience': resume.experience,
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Deleted experience: {deleted_experience.get('title', 'Unknown')} at {deleted_experience.get('company', 'Unknown')}",
                "data": {
                    "resume_id": str(resume.id),
                    "experience_index": experience_index,
                    "deleted_experience": deleted_experience,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in delete_experience: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def save_skills(
        user_id: str,
        resume_id: str,
        technical_skills: list,
        soft_skills: list,
        languages: list
    ) -> Dict[str, Any]:
        """Save skills with comprehensive validation"""
        try:
            print(f"\n========== SAVE SKILLS ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Technical Skills: {technical_skills}")
            print(f"Soft Skills: {soft_skills}")
            print(f"Languages: {languages}")
            
            # Validation: Check if at least some skills are provided
            if (not technical_skills or len(technical_skills) == 0) and \
               (not soft_skills or len(soft_skills) == 0) and \
               (not languages or len(languages) == 0):
                return {
                    "success": False,
                    "error": "Please provide at least some skills (technical skills, soft skills, or languages)",
                    "action": "request_skills_info"
                }
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Clean and validate skills data
            prev_skills = resume.skills or {}
            cleaned_skills = {
                **prev_skills,
                'technical': [skill.strip() for skill in (technical_skills or []) if skill.strip()],
                'soft': [skill.strip() for skill in (soft_skills or []) if skill.strip()],
                'languages': [lang.strip() for lang in (languages or []) if lang.strip()],
            }
            cleaned_skills['rated'] = prev_skills.get('rated', [])
            
            # Update resume - preserve existing data and only update skills
            existing_personal_info = resume.personal_info or {}
            existing_experience = resume.experience or []
            existing_education = resume.education or []
            existing_additional = resume.additional or {}
            
            # Only update the skills section
            resume.skills = cleaned_skills
            
            # Preserve all other sections
            resume.personal_info = existing_personal_info
            resume.experience = existing_experience
            resume.education = existing_education
            resume.additional = existing_additional
            
            resume.save()
            
            # Emit events to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'skills': resume.skills,
                'timestamp': datetime.now().isoformat()
            })
            
            EventEmitter.emit_event(user_id, 'section_completed', {
                'section': 'skills',
                'data': resume.skills,
                'next_section': 'additional',
                'timestamp': datetime.now().isoformat()
            })

            result = {
                "success": True,
                "message": f"## ✅ Skills Saved!\n\n**Technical Skills:** {len(cleaned_skills['technical'])} skills\n**Soft Skills:** {len(cleaned_skills['soft'])} skills\n**Languages:** {len(cleaned_skills['languages'])} languages\n\nPerfect! I've captured your skills. Now let's add any **additional information**.\n\n**What I need from you:**\n• **Certifications:** Professional certifications, licenses, qualifications\n• **Projects:** Personal projects, achievements, additional work\n\nThis section is optional but can make your resume stand out!",
                "data": {
                    "resume_id": str(resume.id),
                    "user_id": str(user.id),
                    "username": user.username,
                    "technical_skills_count": len(cleaned_skills['technical']),
                    "soft_skills_count": len(cleaned_skills['soft']),
                    "languages_count": len(cleaned_skills['languages']),
                    "skills": cleaned_skills,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in save_skills: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def edit_skills(user_id: str, resume_id: str, skill_type: str, skills: list) -> Dict[str, Any]:
        """Edit specific skills categories"""
        try:
            print(f"\n========== EDIT SKILLS ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Skill Type: {skill_type}")
            print(f"Skills: {skills}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Validate skill type
            valid_types = ['technical', 'soft', 'languages']
            if skill_type not in valid_types:
                return {"success": False, "error": f"Invalid skill type. Must be one of: {', '.join(valid_types)}"}
            
            # Update the specific skill type
            current_skills = resume.skills or {}
            current_skills[skill_type] = skills
            resume.skills = current_skills
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'skills': resume.skills,
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Updated {skill_type} skills",
                "data": {
                    "resume_id": str(resume.id),
                    "skill_type": skill_type,
                    "skills": skills,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in edit_skills: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def save_additional(
        user_id: str,
        resume_id: str,
        certifications: str,
        projects: str
    ) -> Dict[str, Any]:
        """Save additional information with validation"""
        try:
            print(f"\n========== SAVE ADDITIONAL ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Certifications: {certifications}")
            print(f"Projects: {projects}")
            
            # Additional info is optional, but if provided, it should have content
            if not certifications or not certifications.strip():
                certifications = ""
            if not projects or not projects.strip():
                projects = ""
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Clean and validate additional data
            cleaned_additional = {
                'certifications': certifications.strip() if certifications else '',
                'projects': projects.strip() if projects else ''
            }
            
            # Update resume - merge into existing additional (preserve references, etc.)
            existing_personal_info = resume.personal_info or {}
            existing_experience = resume.experience or []
            existing_education = resume.education or []
            existing_skills = resume.skills or {}
            
            prev_add = resume.additional or {}
            resume.additional = dict(prev_add, **cleaned_additional)
            
            # Preserve all other sections
            resume.personal_info = existing_personal_info
            resume.experience = existing_experience
            resume.education = existing_education
            resume.skills = existing_skills
            
            resume.save()
            
            # Emit events to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'additional': resume.additional,
                'timestamp': datetime.now().isoformat()
            })
            
            EventEmitter.emit_event(user_id, 'section_completed', {
                'section': 'additional',
                'data': resume.additional,
                'next_section': 'summary',  # Next is summary, not final
                'timestamp': datetime.now().isoformat()
            })

            snap = resume.additional or {}
            result = {
                "success": True,
                "message": f"## ✅ Additional Information Saved!\n\n**Certifications:** {len((snap.get('certifications') or '').strip()) > 0 and 'Added' or 'None provided'}\n**Projects:** {len((snap.get('projects') or '').strip()) > 0 and 'Added' or 'None provided'}\n\nExcellent! Your resume is almost complete. Now I can generate a **professional summary** based on your complete resume content.\n\n**Would you like me to:**\n1. **Generate a summary automatically** - I'll create a compelling summary based on your experience, education, and skills\n2. **Use your own summary** - You can provide your own professional summary\n\nJust let me know which option you prefer!",
                "data": {
                    "resume_id": str(resume.id),
                    "user_id": str(user.id),
                    "username": user.username,
                    "certifications": snap.get('certifications', ''),
                    "projects": snap.get('projects', ''),
                    "additional": snap,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in save_additional: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def edit_additional(user_id: str, resume_id: str, field: str, value: str) -> Dict[str, Any]:
        """Edit additional information fields"""
        try:
            print(f"\n========== EDIT ADDITIONAL ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Field: {field}")
            print(f"Value: {value}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Validate field
            valid_fields = ['certifications', 'projects']
            if field not in valid_fields:
                return {"success": False, "error": f"Invalid field. Must be one of: {', '.join(valid_fields)}"}
            
            # Update the specific field
            additional_info = resume.additional or {}
            additional_info[field] = value
            resume.additional = additional_info
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'additional': resume.additional,
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Updated {field} to: {value}",
                "data": {
                    "resume_id": str(resume.id),
                    "field": field,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in edit_additional: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_resume_info(user_id: str, resume_id: str) -> Dict[str, Any]:
        """Get information about a specific resume"""
        try:
            print(f"\n========== GET RESUME INFO ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            result = {
                "success": True,
                "message": f"Resume info retrieved for '{resume.name}'",
                "data": {
                    "resume_id": str(resume.id),
                    "name": resume.name,
                    "template_id": resume.template_id,
                    "draft": resume.draft,
                    "personal_info": resume.personal_info or {},
                    "experience_count": len(resume.experience or []),
                    "education_count": len(resume.education or []),
                    "skills": resume.skills or {},
                    "additional": resume.additional or {},
                    "created_at": resume.created_at.isoformat() if resume.created_at else None,
                    "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in get_resume_info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def list_user_resumes(user_id: str) -> Dict[str, Any]:
        """List all resumes for the current user and trigger utility tab display"""
        try:
            print(f"\n========== LIST USER RESUMES ==========")
            print(f"User ID: {user_id}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Get all resumes for the user
            resumes = Resume.objects.filter(user=user).order_by('-updated_at')
            
            resume_list = []
            for resume in resumes:
                resume_list.append({
                    "resume_id": str(resume.id),
                    "name": resume.name,
                    "template_id": resume.template_id,
                    "draft": resume.draft,
                    "created_at": resume.created_at.isoformat() if resume.created_at else None,
                    "updated_at": resume.updated_at.isoformat() if resume.updated_at else None
                })
            
            # Emit event to frontend to show resume list in utility tab
            EventEmitter.emit_event(user_id, 'show_resume_list', {
                'resume_count': len(resume_list),
                'resumes': resume_list,
                'timestamp': datetime.now().isoformat()
            })
            
            # Return success message
            result = {
                "success": True,
                "message": f"I found {len(resume_list)} resume(s) in your account. I've loaded them in the Utility tab for you to review.",
                "data": {
                    "resume_count": len(resume_list),
                    "resumes": resume_list,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in list_user_resumes: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def finalize_resume(user_id: str, resume_id: str, template_id: str = "professional") -> Dict[str, Any]:
        """Mark resume as complete and ready"""
        try:
            print(f"\n========== FINALIZE RESUME ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Template ID: {template_id}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Update resume to finalize it
            resume.draft = False
            resume.template_id = template_id
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'template_id': template_id,
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Resume '{resume.name}' finalized successfully with template {template_id}",
                "data": {
                    "resume_id": str(resume.id),
                    "template_id": template_id,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in finalize_resume: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def list_templates(user_id: str) -> Dict[str, Any]:
        """Get all available resume templates from Django view"""
        try:
            print(f"\n========== LIST TEMPLATES ==========")
            print(f"User ID: {user_id}")
            
            # Call the Django view directly (simulate a GET request)
            from django.test import RequestFactory
            from resume_builder.views import get_available_templates

            factory = RequestFactory()
            request = factory.get('/resume_builder/templates/')
            response = get_available_templates(request)
            
            # Extract JSON data from JsonResponse
            if hasattr(response, 'content'):
                import json
                data = json.loads(response.content.decode('utf-8'))
            else:
                # Fallback if response doesn't have content attribute
                data = response.json() if hasattr(response, 'json') else {}

            # Build template list
            template_list = []
            for template in data.get("templates", []):
                template_list.append(f"**{template['name']}** - {template['description']}")
            
            template_text = "\n".join(template_list)
            feature_lines = []
            for t in data.get("templates", []):
                feats = t.get("features") or []
                feat_str = ", ".join(feats) if feats else t.get("description", "")
                feature_lines.append(f"• **{t['name']}:** {feat_str}")
            features_block = "\n".join(feature_lines) if feature_lines else ""

            return {
                "success": data.get("success", False),
                "message": f"## 📋 Available Resume Templates\n\nHere are the templates you can choose from:\n\n{template_text}\n\n**Features:**\n{features_block}\n\nWhich template would you like to use for your resume?",
                "templates": data.get("templates", []),
                "count": data.get("count", 0),
                "action": "list_templates"
            }
        except Exception as e:
            logger.error(f"Error in list_templates: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def preview_template(user_id: str, template_id: str) -> Dict[str, Any]:
        """Preview a resume template without requiring a specific resume"""
        try:
            print(f"\n========== PREVIEW TEMPLATE ==========")
            print(f"User ID: {user_id}")
            print(f"Template ID: {template_id}")
            
            valid_template_ids = get_valid_template_ids()
            if template_id not in valid_template_ids:
                return {
                    "success": False,
                    "error": f"Invalid template ID. Must be one of: {', '.join(valid_template_ids)}"
                }
            
            # Emit event to frontend to switch template preview
            EventEmitter.emit_event(user_id, 'template_preview_changed', {
                'template_id': template_id,
                'action': 'preview_template',
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Template preview switched to {template_id}",
                "data": {
                    "template_id": template_id,
                    "action": "preview_template",
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in preview_template: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def switch_template(user_id: str, resume_id: str, template_id: str) -> Dict[str, Any]:
        """Switch to a different resume template"""
        try:
            print(f"\n========== SWITCH TEMPLATE ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Template ID: {template_id}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Convert user_id to integer using helper method
            try:
                numeric_user_id = FunctionHandlers._convert_to_int(user_id, "user_id")
            except ValueError as e:
                return {"success": False, "error": str(e)}
            
            # Validate user exists
            try:
                user = User.objects.get(id=numeric_user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Convert resume_id to integer using helper method
            try:
                numeric_resume_id = FunctionHandlers._convert_to_int(resume_id, "resume_id")
            except ValueError as e:
                return {"success": False, "error": str(e)}
            
            try:
                resume = Resume.objects.get(id=numeric_resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            valid_template_ids = get_valid_template_ids()
            if template_id not in valid_template_ids:
                return {
                    "success": False,
                    "error": f"Invalid template ID. Must be one of: {', '.join(valid_template_ids)}"
                }
            
            # Update template
            resume.template_id = template_id
            resume.save()

            # Emit event to frontend
            EventEmitter.emit_event(user_id, 'template_changed', {
                'resume_id': str(resume.id),
                'template_id': template_id,
                'action': 'switch_template',
                'timestamp': datetime.now().isoformat()
            })
            
            result = {
                "success": True,
                "message": f"Template switched to {template_id}",
                "data": {
                    "resume_id": str(resume.id),
                    "template_id": template_id,
                    "action": "switch_template",
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in switch_template: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    # Keep some legacy functions for compatibility
    @staticmethod
    def save_email(recipient: str, subject: str, content: str) -> Dict[str, Any]:
        """Legacy email function - kept for compatibility"""
        try:
            print(f"\n========== SAVE EMAIL (LEGACY) ==========")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Content: {content}")
            
            result = {
                "success": True,
                "message": "Email saved as draft",
                "data": {
                    "to": recipient,
                    "subject": subject,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in save_email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def auto_respond_email(recipient: str, subject: str, content: str, original_email: str) -> Dict[str, Any]:
        """Legacy auto-respond email function - kept for compatibility"""
        try:
            print(f"\n========== AUTO RESPOND EMAIL (LEGACY) ==========")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Content: {content}")
            print(f"Original: {original_email}")
            
            result = {
                "success": True,
                "message": "Auto-response sent successfully",
                "data": {
                    "to": recipient,
                    "subject": subject,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in auto_respond_email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def reply_to_email(recipient: str, subject: str, content: str, thread_id: str, quoted_text: str = None) -> Dict[str, Any]:
        """Legacy reply email function - kept for compatibility"""
        try:
            print(f"\n========== REPLY TO EMAIL (LEGACY) ==========")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Content: {content}")
            print(f"Thread ID: {thread_id}")
            print(f"Quoted Text: {quoted_text}")
            
            result = {
                "success": True,
                "message": "Reply sent successfully",
                "data": {
                    "to": recipient,
                    "subject": subject,
                    "content": content,
                    "thread_id": thread_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in reply_to_email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def forward_email(recipient: str, subject: str, content: str, original_email: str) -> Dict[str, Any]:
        """Legacy forward email function - kept for compatibility"""
        try:
            print(f"\n========== FORWARD EMAIL (LEGACY) ==========")
            print(f"To: {recipient}")
            print(f"Subject: {subject}")
            print(f"Content: {content}")
            print(f"Original: {original_email}")
            
            result = {
                "success": True,
                "message": "Email forwarded successfully",
                "data": {
                    "to": recipient,
                    "subject": subject,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in forward_email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 

    @staticmethod
    def save_summary(
        user_id: str,
        resume_id: str,
        summary: str
    ) -> Dict[str, Any]:
        """Generate and save a professional summary based on the complete resume content"""
        try:
            print(f"\n========== SAVE SUMMARY ==========")
            print(f"User ID: {user_id}")
            print(f"Resume ID: {resume_id}")
            print(f"Summary: {summary}")
            
            # Setup Django
            import os
            import django
            from django.conf import settings
            
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
                django.setup()
            
            from resume_builder.models import Resume
            from django.contrib.auth.models import User
            
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Validate resume belongs to user
            try:
                resume = Resume.objects.get(id=resume_id, user=user)
            except Resume.DoesNotExist:
                return {"success": False, "error": f"Resume with ID {resume_id} not found for user {user_id}"}
            
            # Get current personal info and update only the summary
            current_personal_info = resume.personal_info or {}
            current_personal_info['summary'] = summary.strip()
            
            # Update the personal info section with the new summary
            resume.personal_info = current_personal_info
            
            # Preserve all other sections
            existing_experience = resume.experience or []
            existing_education = resume.education or []
            existing_skills = resume.skills or {}
            existing_additional = resume.additional or {}
            
            resume.experience = existing_experience
            resume.education = existing_education
            resume.skills = existing_skills
            resume.additional = existing_additional
            
            resume.save()
            
            # Emit events to frontend
            EventEmitter.emit_event(user_id, 'resume_updated', {
                'resume_id': str(resume.id),
                'personal_info': resume.personal_info,
                'timestamp': datetime.now().isoformat()
            })
            
            EventEmitter.emit_event(user_id, 'section_completed', {
                'section': 'summary',
                'data': {'summary': summary},
                'next_section': None,  # This is the final section
                'timestamp': datetime.now().isoformat()
            })

            result = {
                "success": True,
                "message": f"## 🎉 Resume Complete!\n\n**Professional Summary:** Added successfully\n\nCongratulations! Your resume is now **complete and ready** for review. Here's what you can do next:\n\n**📋 Review Your Resume:**\n• Switch to the **Resume Builder** tab to see your complete resume\n• Review all sections and make sure everything looks correct\n\n**💾 Download Options:**\n• Download as **HTML** for web viewing\n• Download as **PDF** for printing and sharing\n• Download as **Word** document for editing\n\n**🔄 Make Changes:**\n• You can always come back and edit any section\n• Switch between different templates\n• Add more experience or education entries\n\nYour resume is now professional and ready to help you land your next job! 🚀",
                "data": {
                    "resume_id": str(resume.id),
                    "user_id": str(user.id),
                    "username": user.username,
                    "summary": summary,
                    "personal_info": resume.personal_info,
                    "timestamp": datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Error in save_summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 

    @staticmethod
    def get_current_date(user_id: str, format: str = "formal") -> Dict[str, Any]:
        """
        Get the current date in a format suitable for cover letters and formal documents.

        Args:
            user_id: ID of the user requesting the date
            format: Date format preference - "formal", "short", or "numeric"

        Returns:
            dict: Current date in the requested format
        """
        from datetime import datetime
        
        current_date = datetime.now()
        
        if format == "formal":
            formatted_date = current_date.strftime("%B %d, %Y")
        elif format == "short":
            formatted_date = current_date.strftime("%b %d, %Y")
        elif format == "numeric":
            formatted_date = current_date.strftime("%m/%d/%Y")
        else:
            # Default to formal format
            formatted_date = current_date.strftime("%B %d, %Y")
        
        return {
            "success": True,
            "date": formatted_date,
            "format": format,
            "timestamp": current_date.isoformat()
        }

    @staticmethod
    def create_cover_letter(user_id: str, cover_letter_name: str) -> Dict[str, Any]:
        """
        Create a new cover letter for the user.

        Args:
            user_id: ID of the user creating the cover letter
            cover_letter_name: Name for the cover letter

        Returns:
            dict: Result of cover letter creation
        """
        try:
            from coverletter.models import CoverLetter
            
            # Create the cover letter
            cover_letter = CoverLetter.objects.create(
                user_id=user_id,
                title=cover_letter_name,
                status='pending'
            )
            
            # Emit event to frontend
            EventEmitter.emit_event(
                user_id=user_id,
                event_type="cover_letter_created",
                data={
                    "cover_letter_id": str(cover_letter.id),
                    "cover_letter_name": cover_letter.title,
                    "user_id": user_id
                }
            )
            
            return {
                "success": True,
                "cover_letter_id": str(cover_letter.id),
                "cover_letter_name": cover_letter.title,
                "message": f"Cover letter '{cover_letter_name}' created successfully."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create cover letter: {str(e)}"
            }

    @staticmethod
    def save_cover_letter_user_info(user_id: str, cover_letter_id: str, full_name: str, address: str, email: str, phone: str) -> Dict[str, Any]:
        """
        Save user information for cover letter.

        Args:
            user_id: ID of the user
            cover_letter_id: ID of the cover letter to update
            full_name: Full name of the person
            address: Address (City, State/Country)
            email: Email address
            phone: Phone number

        Returns:
            dict: Result of saving user info
        """
        try:
            from coverletter.models import CoverLetter
            
            # Validate required fields
            if not all([full_name, address, email, phone]):
                return {
                    "success": False,
                    "error": "All fields (full_name, address, email, phone) are required."
                }
            
            # Get the cover letter
            try:
                cover_letter = CoverLetter.objects.get(id=cover_letter_id, user_id=user_id)
            except CoverLetter.DoesNotExist:
                return {
                    "success": False,
                    "error": f"Cover letter with ID {cover_letter_id} not found."
                }
            
            # Store user info in content field as structured data
            user_info = {
                "full_name": full_name,
                "address": address,
                "email": email,
                "phone": phone
            }
            
            # Update the cover letter content with user info
            current_content = cover_letter.content or "{}"
            try:
                content_data = eval(current_content) if current_content else {}
            except:
                content_data = {}
            
            content_data['user_info'] = user_info
            cover_letter.content = str(content_data)
            cover_letter.save()
            
            # Emit event to frontend
            EventEmitter.emit_event(
                user_id=user_id,
                event_type="cover_letter_user_info_saved",
                data={
                    "cover_letter_id": str(cover_letter.id),
                    "user_info": user_info,
                    "user_id": user_id
                }
            )
            
            return {
                "success": True,
                "message": "User information saved successfully.",
                "user_info": user_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save user info: {str(e)}"
            }

    @staticmethod
    def save_cover_letter_employer_info(user_id: str, cover_letter_id: str, company_name: str, position_title: str, hiring_manager: str = None, company_address: str = None) -> Dict[str, Any]:
        """
        Save employer information for cover letter.

        Args:
            user_id: ID of the user
            cover_letter_id: ID of the cover letter to update
            company_name: Name of the company
            position_title: Title of the position being applied for
            hiring_manager: Name of hiring manager (optional)
            company_address: Company address (optional)

        Returns:
            dict: Result of saving employer info
        """
        try:
            from coverletter.models import CoverLetter
            
            # Validate required fields
            if not all([company_name, position_title]):
                return {
                    "success": False,
                    "error": "Company name and position title are required."
                }
            
            # Get the cover letter
            try:
                cover_letter = CoverLetter.objects.get(id=cover_letter_id, user_id=user_id)
            except CoverLetter.DoesNotExist:
                return {
                    "success": False,
                    "error": f"Cover letter with ID {cover_letter_id} not found."
                }
            
            # Store employer info in content field
            employer_info = {
                "company_name": company_name,
                "position_title": position_title,
                "hiring_manager": hiring_manager or "",
                "company_address": company_address or ""
            }
            
            # Update the cover letter content with employer info
            current_content = cover_letter.content or "{}"
            try:
                content_data = eval(current_content) if current_content else {}
            except:
                content_data = {}
            
            content_data['employer_info'] = employer_info
            cover_letter.content = str(content_data)
            cover_letter.save()
            
            # Emit event to frontend
            EventEmitter.emit_event(
                user_id=user_id,
                event_type="cover_letter_employer_info_saved",
                data={
                    "cover_letter_id": str(cover_letter.id),
                    "employer_info": employer_info,
                    "user_id": user_id
                }
            )
            
            return {
                "success": True,
                "message": "Employer information saved successfully.",
                "employer_info": employer_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save employer info: {str(e)}"
            }

    @staticmethod
    def save_cover_letter_greeting(user_id: str, cover_letter_id: str, greeting: str) -> Dict[str, Any]:
        """
        Save the greeting/salutation for the cover letter.

        Args:
            user_id: ID of the user
            cover_letter_id: ID of the cover letter to update
            greeting: The greeting text (e.g., "Dear Hiring Manager," or "Dear Mr. Smith,")

        Returns:
            dict: Result of saving greeting
        """
        try:
            from coverletter.models import CoverLetter
            
            # Validate required fields
            if not greeting:
                return {
                    "success": False,
                    "error": "Greeting text is required."
                }
            
            # Get the cover letter
            try:
                cover_letter = CoverLetter.objects.get(id=cover_letter_id, user_id=user_id)
            except CoverLetter.DoesNotExist:
                return {
                    "success": False,
                    "error": f"Cover letter with ID {cover_letter_id} not found."
                }
            
            # Store greeting in content field
            current_content = cover_letter.content or "{}"
            try:
                content_data = eval(current_content) if current_content else {}
            except:
                content_data = {}
            
            content_data['greeting'] = greeting
            cover_letter.content = str(content_data)
            cover_letter.save()
            
            # Emit event to frontend
            EventEmitter.emit_event(
                user_id=user_id,
                event_type="cover_letter_greeting_saved",
                data={
                    "cover_letter_id": str(cover_letter.id),
                    "greeting": greeting,
                    "user_id": user_id
                }
            )
            
            return {
                "success": True,
                "message": "Greeting saved successfully.",
                "greeting": greeting
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save greeting: {str(e)}"
            }

    @staticmethod
    def save_cover_letter_introduction(user_id: str, cover_letter_id: str, introduction: str) -> Dict[str, Any]:
        """
        Save the introduction paragraph for the cover letter.

        Args:
            user_id: ID of the user
            cover_letter_id: ID of the cover letter to update
            introduction: The introduction paragraph text

        Returns:
            dict: Result of saving introduction
        """
        try:
            from coverletter.models import CoverLetter
            
            # Validate required fields
            if not introduction:
                return {
                    "success": False,
                    "error": "Introduction text is required."
                }
            
            # Get the cover letter
            try:
                cover_letter = CoverLetter.objects.get(id=cover_letter_id, user_id=user_id)
            except CoverLetter.DoesNotExist:
                return {
                    "success": False,
                    "error": f"Cover letter with ID {cover_letter_id} not found."
                }
            
            # Store introduction in content field
            current_content = cover_letter.content or "{}"
            try:
                content_data = eval(current_content) if current_content else {}
            except:
                content_data = {}
            
            content_data['introduction'] = introduction
            cover_letter.content = str(content_data)
            cover_letter.save()
            
            # Emit event to frontend
            EventEmitter.emit_event(
                user_id=user_id,
                event_type="cover_letter_introduction_saved",
                data={
                    "cover_letter_id": str(cover_letter.id),
                    "introduction": introduction,
                    "user_id": user_id
                }
            )
            
            return {
                "success": True,
                "message": "Introduction saved successfully.",
                "introduction": introduction
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save introduction: {str(e)}"
            }

    @staticmethod
    def save_cover_letter_body(user_id: str, cover_letter_id: str, body: str) -> Dict[str, Any]:
        """
        Save the main body content for the cover letter.

        Args:
            user_id: ID of the user
            cover_letter_id: ID of the cover letter to update
            body: The main body content of the cover letter

        Returns:
            dict: Result of saving body content
        """
        try:
            from coverletter.models import CoverLetter
            
            # Validate required fields
            if not body:
                return {
                    "success": False,
                    "error": "Body content is required."
                }
            
            # Get the cover letter
            try:
                cover_letter = CoverLetter.objects.get(id=cover_letter_id, user_id=user_id)
            except CoverLetter.DoesNotExist:
                return {
                    "success": False,
                    "error": f"Cover letter with ID {cover_letter_id} not found."
                }
            
            # Store body in content field
            current_content = cover_letter.content or "{}"
            try:
                content_data = eval(current_content) if current_content else {}
            except:
                content_data = {}
            
            content_data['body'] = body
            cover_letter.content = str(content_data)
            cover_letter.save()
            
            # Emit event to frontend
            EventEmitter.emit_event(
                user_id=user_id,
                event_type="cover_letter_body_saved",
                data={
                    "cover_letter_id": str(cover_letter.id),
                    "body": body,
                    "user_id": user_id
                }
            )
            
            return {
                "success": True,
                "message": "Body content saved successfully.",
                "body": body
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save body content: {str(e)}"
            }

    @staticmethod
    def finalize_cover_letter(user_id: str, cover_letter_id: str) -> Dict[str, Any]:
        """
        Mark a cover letter as complete and ready for use.

        Args:
            user_id: ID of the user
            cover_letter_id: ID of the cover letter to finalize

        Returns:
            dict: Result of finalizing cover letter
        """
        try:
            from coverletter.models import CoverLetter
            
            # Get the cover letter
            try:
                cover_letter = CoverLetter.objects.get(id=cover_letter_id, user_id=user_id)
            except CoverLetter.DoesNotExist:
                return {
                    "success": False,
                    "error": f"Cover letter with ID {cover_letter_id} not found."
                }
            
            # Check if all required sections are complete
            current_content = cover_letter.content or "{}"
            try:
                content_data = eval(current_content) if current_content else {}
            except:
                content_data = {}
            
            required_sections = ['user_info', 'employer_info', 'greeting', 'introduction', 'body']
            missing_sections = [section for section in required_sections if section not in content_data or not content_data[section]]
            
            if missing_sections:
                return {
                    "success": False,
                    "error": f"Missing required sections: {', '.join(missing_sections)}"
                }
            
            # Mark as completed
            cover_letter.status = 'completed'
            cover_letter.save()
            
            # Emit event to frontend
            EventEmitter.emit_event(
                user_id=user_id,
                event_type="cover_letter_finalized",
                data={
                    "cover_letter_id": str(cover_letter.id),
                    "user_id": user_id
                }
            )
            
            return {
                "success": True,
                "message": "Cover letter finalized successfully.",
                "cover_letter_id": str(cover_letter.id)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to finalize cover letter: {str(e)}"
            } 