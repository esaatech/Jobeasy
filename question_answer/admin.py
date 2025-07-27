from django.contrib import admin
from .models import Category, QuestionType, Question, Answer, InterviewAssistant

# Register your models here.
admin.site.register(Category)
admin.site.register(QuestionType)
admin.site.register(Question)
admin.site.register(Answer)

@admin.register(InterviewAssistant)
class InterviewAssistantAdmin(admin.ModelAdmin):
    list_display = ['user', 'interview_thread_id', 'created_at', 'last_used']
    list_filter = ['created_at', 'last_used']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'last_used']
    
    def has_add_permission(self, request):
        # InterviewAssistant objects are created automatically
        return False
