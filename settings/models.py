from django.db import models
from django.conf import settings

# Create your models here.

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    desktop_notifications = models.BooleanField(default=True)
    
    # Theme Preferences
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default')
    ])
    
    # Language Preferences
    language = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French')
    ])
    
    # Dashboard Preferences
    default_dashboard_view = models.CharField(max_length=20, default='grid', choices=[
        ('grid', 'Grid View'),
        ('list', 'List View')
    ])
    
    # Time Zone
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Date Format
    date_format = models.CharField(max_length=20, default='MM/DD/YYYY')
    time_format = models.CharField(max_length=20, default='12h')
    
    class Meta:
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f"{self.user.username}'s preferences"

class IntegrationSetting(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='integration_settings')
    platform = models.CharField(max_length=50)  # e.g., 'slack', 'teams', 'whatsapp'
    is_active = models.BooleanField(default=False)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    webhook_url = models.URLField(blank=True, null=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'platform']
        verbose_name = 'Integration Setting'
        verbose_name_plural = 'Integration Settings'

    def __str__(self):
        return f"{self.user.username}'s {self.platform} integration"
