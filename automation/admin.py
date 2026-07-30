from django.contrib import admin

from .models import UltimateAutomationProfile


@admin.register(UltimateAutomationProfile)
class UltimateAutomationProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'auto_apply_enabled',
        'title_family_confirmed',
        'title_family_ai_generations',
        'setup_completed',
        'max_applications_per_day',
        'updated_at',
    ]
    list_filter = ['auto_apply_enabled', 'title_family_confirmed', 'setup_completed']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'created_at',
        'updated_at',
        'title_family_confirmed_at',
        'title_family_ai_generations',
    ]
    raw_id_fields = ['default_resume']
