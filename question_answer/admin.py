from django.contrib import admin
from .models import QuestionType, Question, Answer

# Register your models here.
admin.site.register(QuestionType)
admin.site.register(Question)
admin.site.register(Answer)
