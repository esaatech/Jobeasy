from django.contrib import admin
from django.contrib import messages
from django.db.models import Count

from .models import Category, QuestionType, Question, Answer, InterviewAssistant


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('text', 'type', 'order', 'options', 'user')
    show_change_link = True
    autocomplete_fields = ('type',)
    raw_id_fields = ('user',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'type':
            essay = QuestionType.objects.filter(name='Essay').first()
            if essay is not None:
                kwargs.setdefault('initial', essay.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'question_count', 'description_preview')
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = (QuestionInline,)
    fieldsets = (
        (
            None,
            {
                'fields': ('name', 'description'),
                'description': (
                    'Each category appears as an option on interview prep (e.g. behavioral themes '
                    'like Leadership, or a role track such as Frontend Developer). '
                    'Use one consistent name per profession.'
                ),
            },
        ),
    )

    @admin.display(description='Questions')
    def question_count(self, obj):
        if hasattr(obj, '_question_count'):
            return obj._question_count
        return obj.questions.count()

    @admin.display(description='Description')
    def description_preview(self, obj):
        if not obj.description:
            return '—'
        text = obj.description.strip()
        return text[:80] + ('…' if len(text) > 80 else '')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_question_count=Count('questions'))

    def delete_model(self, request, obj):
        general = Category.get_general()
        if obj.pk == general.pk:
            self.message_user(
                request,
                'The "General" category cannot be deleted; it is the default for interview prep.',
                level=messages.ERROR,
            )
            return
        Question.objects.filter(category=obj).update(category=general)
        super().delete_model(request, obj)
        self.message_user(
            request,
            f'Category deleted. Its questions were moved to "{general.name}".',
            level=messages.SUCCESS,
        )

    def delete_queryset(self, request, queryset):
        general = Category.get_general()
        rest = queryset.exclude(pk=general.pk)
        skipped = queryset.filter(pk=general.pk).exists()
        if skipped:
            self.message_user(
                request,
                'Skipped deleting the "General" category.',
                level=messages.WARNING,
            )
        if rest.exists():
            Question.objects.filter(category__in=rest).update(category=general)
            deleted, _ = rest.delete()
            self.message_user(
                request,
                f'{deleted} categor(y/ies) deleted; their questions were moved to "{general.name}".',
                level=messages.SUCCESS,
            )


@admin.register(QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_name')
    search_fields = ('name', 'description')


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('user', 'answer_text', 'is_correct', 'score', 'submitted_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'category', 'type', 'order', 'user')
    list_filter = ('category', 'type')
    search_fields = ('text',)
    ordering = ('category__name', 'order', 'id')
    autocomplete_fields = ('category', 'type')
    raw_id_fields = ('user',)
    fieldsets = (
        (
            None,
            {
                'fields': ('category', 'type', 'text', 'order', 'user'),
            },
        ),
        (
            'Options (JSON)',
            {
                'fields': ('options',),
                'description': (
                    'Interview prep sample answers: '
                    '<code>{"sample_answer": "...", "question_type": "interview_prep"}</code>'
                ),
            },
        ),
    )
    inlines = (AnswerInline,)

    @admin.display(description='Question')
    def text_preview(self, obj):
        text = (obj.text or '').strip().replace('\n', ' ')
        return text[:70] + ('…' if len(text) > 70 else '')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'score', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('user__username', 'question__text')
    autocomplete_fields = ('question',)
    raw_id_fields = ('user',)
    readonly_fields = ('submitted_at',)


@admin.register(InterviewAssistant)
class InterviewAssistantAdmin(admin.ModelAdmin):
    list_display = ['user', 'interview_thread_id', 'created_at', 'last_used']
    list_filter = ['created_at', 'last_used']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'last_used']

    def has_add_permission(self, request):
        return False
