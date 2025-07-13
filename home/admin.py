from django.contrib import admin
from .models import CoverLetterInstruction, FAQ, Testimonial, NewsletterSignup, ContactMessage, JobOpening

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

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'published')
    search_fields = ('question', 'answer')
    list_filter = ('published',)
    ordering = ('order',)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'quote', 'published')
    search_fields = ('name', 'quote')
    list_filter = ('published',)

@admin.register(NewsletterSignup)
class NewsletterSignupAdmin(admin.ModelAdmin):
    list_display = ('email', 'date')
    search_fields = ('email',)
    ordering = ('-date',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'date')
    search_fields = ('name', 'email', 'message')
    ordering = ('-date',)

admin.site.register(JobOpening)
