from django.contrib import admin
from .models import EmailLog

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'subject', 'template_name', 'sent_at', 'success']
    list_filter = ['success', 'sent_at', 'template_name']
    search_fields = ['recipient', 'subject']
    readonly_fields = ['sent_at']
    ordering = ['-sent_at']
    
    fieldsets = (
        ('Email Details', {
            'fields': ('recipient', 'subject', 'template_name')
        }),
        ('Status', {
            'fields': ('success', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('sent_at',),
            'classes': ('collapse',)
        }),
    )

