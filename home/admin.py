from django.contrib import admin
from .models import CoverLetterInstruction

@admin.register(CoverLetterInstruction)
class CoverLetterInstructionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'updated_at')
    search_fields = ('title', 'greeting', 'focus', 'understanding', 'enthusiasm', 'examples', 'tone', 'closing', 'no_dates', 'length_limit')
    ordering = ('-updated_at',)
    fieldsets = (
        (None, {
            'fields': ('title',)
        }),
        ('Instructions', {
            'fields': (
                'greeting',
                'focus',
                'understanding',
                'enthusiasm',
                'examples',
                'tone',
                'closing',
                'no_dates',
                'length_limit',
            )
        }),
    )
