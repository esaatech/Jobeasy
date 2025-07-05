from django.db import models
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @staticmethod
    def get_general():
        category, _ = Category.objects.get_or_create(name='General', defaults={'description': 'General purpose questions'})
        return category

class QuestionType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    template_name = models.CharField(max_length=100, help_text='Template partial for this type (e.g., question_types/multiple_choice.html)')

    def __str__(self):
        return self.name

class Question(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='qa_questions', help_text='If set, this question is private to the user. If null, it is global.')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions', default=None)
    text = models.TextField()
    type = models.ForeignKey(QuestionType, on_delete=models.CASCADE, related_name='questions')
    options = models.JSONField(blank=True, null=True, help_text='For MCQ, True/False, etc. Store choices as a list or dict.')
    order = models.PositiveIntegerField(default=1)
    # For reusability, allow linking to any session/parent via GenericForeignKey if needed later

    def save(self, *args, **kwargs):
        if self.category is None:
            self.category = Category.get_general()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.text[:50]}... ({self.type.name})"

class Answer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='qa_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    is_correct = models.BooleanField(null=True, blank=True)
    score = models.FloatField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.user.username} to Q{self.question.id}"
