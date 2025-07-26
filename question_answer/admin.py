from django.contrib import admin
from .models import Category, QuestionType, Question, Answer

# Register your models here.
admin.site.register(Category)
admin.site.register(QuestionType)
admin.site.register(Question)
admin.site.register(Answer)
