from django.contrib import admin
from .models import ResumeTemplate


@admin.register(ResumeTemplate)
class ResumeTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "template_id",
        "name",
        "role_label",
        "gallery_section",
        "featured",
        "featured_rank",
        "is_active",
        "updated_at",
    )
    search_fields = ("template_id", "name", "description", "role_label", "short_label")
    list_filter = ("gallery_section", "featured", "is_active")
    ordering = ("featured_rank", "name")
