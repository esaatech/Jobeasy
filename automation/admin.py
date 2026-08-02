from django.contrib import admin

from .models import UltimateAutomationProfile


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
