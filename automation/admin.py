from django.contrib import admin
from django.utils.html import format_html

from .models import ApplyTask, UltimateAutomationProfile


@admin.register(UltimateAutomationProfile)
class UltimateAutomationProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'auto_apply_enabled',
        'title_family_confirmed',
        'city',
        'max_applications_per_day',
        'setup_completed',
        'updated_at',
    ]
    list_filter = ['auto_apply_enabled', 'title_family_confirmed', 'setup_completed', 'search_purpose']
    search_fields = ['user__username', 'user__email', 'city']
    readonly_fields = [
        'created_at',
        'updated_at',
        'title_family_confirmed_at',
        'title_family_ai_generations',
    ]
    raw_id_fields = ['default_resume']
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'primary_titles',
                'related_titles',
                'exclude_titles',
                'default_resume',
                'auto_apply_enabled',
                'max_applications_per_day',
            )
        }),
        ('Search preferences', {
            'fields': (
                'search_purpose',
                'other_purpose',
                'preferred_countries',
                'city',
                'distance_miles',
                'work_arrangements',
            )
        }),
        ('Status', {
            'fields': (
                'title_family_confirmed',
                'title_family_confirmed_at',
                'title_family_ai_generations',
                'setup_completed',
                'created_at',
                'updated_at',
            )
        }),
    )


@admin.register(ApplyTask)
class ApplyTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'job_title',
        'company',
        'status',
        'application_link',
        'created_at',
        'applied_at',
    ]
    list_filter = ['status', 'skip_reason', 'created_at']
    search_fields = [
        'user__username',
        'user__email',
        'job__title',
        'job__company',
        'application_url',
    ]
    readonly_fields = ['created_at', 'updated_at', 'applied_at']
    raw_id_fields = ['user', 'job']
    ordering = ['-created_at']
    list_select_related = ['user', 'job']

    fieldsets = (
        (None, {
            'fields': ('user', 'job', 'application_url', 'status'),
        }),
        ('Operator', {
            'fields': ('skip_reason', 'operator_notes', 'applied_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Job title', ordering='job__title')
    def job_title(self, obj):
        return obj.job.title if obj.job_id else '—'

    @admin.display(description='Company', ordering='job__company')
    def company(self, obj):
        return obj.job.company if obj.job_id else '—'

    @admin.display(description='Apply URL')
    def application_link(self, obj):
        if not obj.application_url:
            return '—'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Open</a>',
            obj.application_url,
        )
