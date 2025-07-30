from django.contrib import admin
from .models import GmailAuth, EmailHistory


@admin.register(GmailAuth)
class GmailAuthAdmin(admin.ModelAdmin):
    list_display = ['user', 'gmail_address', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'gmail_address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'gmail_address', 'is_active')
        }),
        ('OAuth2 Tokens', {
            'fields': ('access_token', 'refresh_token', 'token_expiry'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailHistory)
class EmailHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipient_email', 'subject', 'attachment_type', 'status', 'sent_at']
    list_filter = ['status', 'attachment_type', 'sent_at']
    search_fields = ['user__username', 'user__email', 'recipient_email', 'subject']
    readonly_fields = ['sent_at', 'gmail_message_id']
    
    fieldsets = (
        ('Email Information', {
            'fields': ('user', 'recipient_email', 'subject', 'message')
        }),
        ('Attachment Information', {
            'fields': ('attachment_type', 'attachment_id')
        }),
        ('Status Information', {
            'fields': ('status', 'gmail_message_id', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('sent_at',),
            'classes': ('collapse',)
        }),
    )

