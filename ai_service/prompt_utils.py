"""
Utility functions for retrieving AI prompts from the database.
This module provides a way to get configurable system prompts without modifying existing code.
"""

from .models import AIService, AIPromptConfiguration


def get_ai_prompt(service_slug, prompt_slug='default', fallback_to_default=True):
    """
    Get AI prompt configuration from database with fallback support.
    
    Args:
        service_slug (str): The service identifier (e.g., 'cover_letter', 'resume_optimization')
        prompt_slug (str): The prompt variant identifier (e.g., 'default', 'with_email_subject')
        fallback_to_default (bool): Whether to fall back to default prompt if specific one not found
    
    Returns:
        str: The system prompt, or None if not found
    """
    try:
        # Try to get the specific prompt
        prompt = AIPromptConfiguration.objects.get(
            service__slug=service_slug,
            slug=prompt_slug,
            is_active=True
        )
        return prompt.system_prompt
    except AIPromptConfiguration.DoesNotExist:
        if fallback_to_default and prompt_slug != 'default':
            # Fall back to default prompt
            try:
                default_prompt = AIPromptConfiguration.objects.get(
                    service__slug=service_slug,
                    is_default=True,
                    is_active=True
                )
                return default_prompt.system_prompt
            except AIPromptConfiguration.DoesNotExist:
                pass
        
        # Return None if no prompt found
        return None


def get_ai_service_prompts(service_slug):
    """
    Get all active prompts for a specific service.
    
    Args:
        service_slug (str): The service identifier
    
    Returns:
        list: List of prompt configurations for the service
    """
    try:
        return list(AIPromptConfiguration.objects.filter(
            service__slug=service_slug,
            is_active=True
        ).order_by('-is_default', 'name'))
    except Exception:
        return []


def is_service_available(service_slug):
    """
    Check if a service is available and has active prompts.
    
    Args:
        service_slug (str): The service identifier
    
    Returns:
        bool: True if service exists and has active prompts
    """
    try:
        return AIService.objects.filter(
            slug=service_slug,
            is_active=True,
            prompts__is_active=True
        ).exists()
    except Exception:
        return False


def get_all_services():
    """
    Get all active AI services.
    
    Returns:
        list: List of active AI services
    """
    try:
        return list(AIService.objects.filter(is_active=True).order_by('name'))
    except Exception:
        return []
