from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AIService, AIPromptConfiguration

# Register your models here.

@admin.register(AIService)
class AIServiceAdmin(admin.ModelAdmin):
    """Admin interface for AI Service model."""
    list_display = ['name', 'slug', 'is_active', 'prompt_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def prompt_count(self, obj):
        """Display the number of prompts for this service."""
        count = obj.prompts.count()
        if count > 0:
            url = reverse('admin:ai_service_aipromptconfiguration_changelist') + f'?service__id__exact={obj.id}'
            return format_html('<a href="{}">{} prompt{}</a>', url, count, 's' if count != 1 else '')
        return '0 prompts'
    prompt_count.short_description = 'Prompts'
    
    def get_queryset(self, request):
        """Optimize queryset with prompt count."""
        return super().get_queryset(request).prefetch_related('prompts')


class AIPromptConfigurationInline(admin.TabularInline):
    """Inline admin for prompt configurations within AI Service admin."""
    model = AIPromptConfiguration
    extra = 1
    fields = ['name', 'slug', 'is_active', 'is_default']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AIPromptConfiguration)
class AIPromptConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for AI Prompt Configuration model."""
    list_display = ['service', 'name', 'slug', 'is_active', 'is_default', 'updated_at', 'preview_link']
    list_filter = ['service', 'is_active', 'is_default', 'created_at', 'updated_at']
    search_fields = ['service__name', 'name', 'slug', 'system_prompt']
    readonly_fields = ['created_at', 'updated_at', 'preview_system_prompt']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('service', 'name', 'slug')
        }),
        ('Prompt Content', {
            'fields': ('system_prompt', 'preview_system_prompt'),
            'description': 'Enter the system prompt that will be sent to the AI. Use the preview below to see how it will look.'
        }),
        ('Status', {
            'fields': ('is_active', 'is_default'),
            'description': 'Only one prompt per service can be the default. Setting this as default will unset others.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_system_prompt(self, obj):
        """Show a preview of the system prompt."""
        if obj.system_prompt:
            # Truncate and format the preview
            preview = obj.system_prompt[:200] + '...' if len(obj.system_prompt) > 200 else obj.system_prompt
            return format_html(
                '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; max-height: 200px; overflow-y: auto;">{}</div>',
                preview
            )
        return 'No prompt content'
    preview_system_prompt.short_description = 'Prompt Preview'
    
    def preview_link(self, obj):
        """Link to preview the full prompt."""
        if obj.system_prompt:
            return format_html(
                '<a href="#" onclick="alert(\'{}\'); return false;">Preview</a>',
                obj.system_prompt.replace("'", "\\'").replace('\n', '\\n')
            )
        return '-'
    preview_link.short_description = 'Preview'
    
    def get_queryset(self, request):
        """Optimize queryset with service information."""
        return super().get_queryset(request).select_related('service')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter services to only show active ones."""
        if db_field.name == "service":
            kwargs["queryset"] = AIService.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Custom save logic to handle default prompt logic."""
        super().save_model(request, obj, form, change)
        
        # Show a message if this is now the default
        if obj.is_default:
            self.message_user(
                request,
                f'"{obj.name}" is now the default prompt for "{obj.service.name}". Other prompts for this service are no longer default.',
                level='INFO'
            )


# Add inline to AIService admin
AIServiceAdmin.inlines = [AIPromptConfigurationInline]
