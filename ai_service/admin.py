import json

from django.conf import settings
from django.contrib import admin, messages
from django.core.serializers.json import DjangoJSONEncoder
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
)
from django.shortcuts import get_object_or_404, redirect
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .admin_resume_pdf import AdminResumePdfExtractMixin, resolve_resume_text_from_admin_request
from .forms import ResumeJobEvaluationAdminForm, WhyShouldIApplyPlaygroundAdminForm
from .models import (
    AIModel,
    AIService,
    AIPromptConfiguration,
    JobFitGateSettings,
    ResumeJobEvaluation,
    WhyShouldIApplyPlayground,
)
from .resume_job_evaluation import RESUME_JOB_EVALUATION_SERVICE_SLUG
from .platform_version import AI_PLATFORM_BUILD
from .resume_job_evaluation import (
    evaluate_resume_against_job,
    get_default_prompt_config,
    parse_pending_evaluation_result,
    persist_resume_job_evaluation_result,
    resolve_prompt_config,
)
from .why_should_i_apply import (
    WHY_SHOULD_I_APPLY_SERVICE_SLUG,
    generate_why_should_i_apply,
    get_default_prompt_config as get_why_apply_default_prompt_config,
    parse_pending_generation_result,
    persist_why_should_i_apply_result,
    resolve_prompt_config as resolve_why_apply_prompt_config,
)


# Register your models here.

# Visible proof-of-deploy in admin (build id also logged by check_ai_platform).
admin.site.site_header = f"Jobeas administration (AI platform {AI_PLATFORM_BUILD})"


@admin.register(JobFitGateSettings)
class JobFitGateSettingsAdmin(admin.ModelAdmin):
    """Singleton: changelist redirects to the single settings row."""

    list_display = [
        "is_enabled",
        "green_min_score",
        "yellow_min_score",
        "prompt_config",
        "updated_at",
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "prompt_config":
            kwargs["queryset"] = AIPromptConfiguration.objects.filter(
                is_active=True,
                service__slug=RESUME_JOB_EVALUATION_SERVICE_SLUG,
                service__is_active=True,
            ).select_related("ai_model")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return not JobFitGateSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        from .job_fit_settings import ensure_job_fit_gate_settings

        obj = ensure_job_fit_gate_settings()
        return redirect(
            reverse("admin:ai_service_jobfitgatesettings_change", args=(obj.pk,))
        )


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'model_id',
        'provider',
        'is_active',
        'sort_order',
        'default_temperature',
    ]
    list_filter = ['provider', 'is_active']
    search_fields = ['display_name', 'model_id', 'description']
    ordering = ['sort_order', 'display_name']


@admin.register(AIService)
class AIServiceAdmin(admin.ModelAdmin):
    """Admin interface for AI Service model."""
    list_display = ['name', 'slug', 'is_active', 'prompt_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def prompt_count(self, obj):
        """Display the number of prompts for this service."""
        count = obj.prompts.count()
        if count > 0:
            url = reverse('admin:ai_service_aipromptconfiguration_changelist') + f'?service__id__exact={obj.id}'
            return format_html('<a href="{}">{} prompt{}</a>', url, count, 's' if count != 1 else '')
        return '0 prompts'
    prompt_count.short_description = 'Prompts'
    
    def get_queryset(self, request):
        """Optimize queryset with prompt count."""
        return super().get_queryset(request).prefetch_related('prompts')


class AIPromptConfigurationInline(admin.TabularInline):
    """Inline admin for prompt configurations within AI Service admin."""
    model = AIPromptConfiguration
    extra = 1
    fields = ['name', 'slug', 'is_active', 'is_default']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AIPromptConfiguration)
class AIPromptConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for AI Prompt Configuration model."""
    list_display = [
        'service',
        'name',
        'slug',
        'ai_model',
        'temperature',
        'is_active',
        'is_default',
        'updated_at',
        'preview_link',
    ]
    list_filter = ['service', 'is_active', 'is_default', 'created_at', 'updated_at']
    search_fields = ['service__name', 'name', 'slug', 'system_prompt']
    readonly_fields = ['created_at', 'updated_at', 'preview_system_prompt']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('service', 'name', 'slug')
        }),
        ('Prompt Content', {
            'fields': ('system_prompt', 'preview_system_prompt'),
            'description': 'Enter the system prompt that will be sent to the AI. Use the preview below to see how it will look.'
        }),
        ('Generation', {
            'fields': ('ai_model', 'temperature'),
            'description': 'Default model and temperature for runs using this prompt variant.',
        }),
        ('Status', {
            'fields': ('is_active', 'is_default'),
            'description': 'Only one prompt per service can be the default. Setting this as default will unset others.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_system_prompt(self, obj):
        """Show a preview of the system prompt."""
        if obj.system_prompt:
            # Truncate and format the preview
            preview = obj.system_prompt[:200] + '...' if len(obj.system_prompt) > 200 else obj.system_prompt
            return format_html(
                '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; max-height: 200px; overflow-y: auto;">{}</div>',
                preview
            )
        return 'No prompt content'
    preview_system_prompt.short_description = 'Prompt Preview'
    
    def preview_link(self, obj):
        """Link to preview the full prompt."""
        if obj.system_prompt:
            return format_html(
                '<a href="#" onclick="alert(\'{}\'); return false;">Preview</a>',
                obj.system_prompt.replace("'", "\\'").replace('\n', '\\n')
            )
        return '-'
    preview_link.short_description = 'Preview'
    
    def get_queryset(self, request):
        """Optimize queryset with service information."""
        return super().get_queryset(request).select_related('service', 'ai_model')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter services to only show active ones."""
        if db_field.name == "service":
            kwargs["queryset"] = AIService.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Custom save logic to handle default prompt logic."""
        super().save_model(request, obj, form, change)
        
        # Show a message if this is now the default
        if obj.is_default:
            self.message_user(
                request,
                f'"{obj.name}" is now the default prompt for "{obj.service.name}". Other prompts for this service are no longer default.',
                level='INFO'
            )


# Add inline to AIService admin
AIServiceAdmin.inlines = [AIPromptConfigurationInline]


@admin.register(ResumeJobEvaluation)
class ResumeJobEvaluationAdmin(AdminResumePdfExtractMixin, admin.ModelAdmin):
    """Playground: save = draft inputs; separate button runs Gemini (prompt test cycle)."""

    form = ResumeJobEvaluationAdminForm
    change_form_template = "admin/ai_service/resumejobevaluation/change_form.html"
    add_form_template = "admin/ai_service/resumejobevaluation/add_form.html"
    list_display = [
        'display_name',
        'recommendation',
        'overall_score',
        'gemini_model',
        'short_description',
        'short_conclusion',
        'succeeded',
        'created_at',
    ]
    list_filter = ['succeeded', 'instruction_slug', 'gemini_model', 'created_at']
    search_fields = [
        'name',
        'description',
        'conclusion',
        'recommendation',
        'job_description',
    ]
    autocomplete_fields = ['prompt_config']

    readonly_fields = [
        '_results_header',
        'ro_succeeded',
        'ro_gemini_model',
        'ro_temperature',
        'ro_instruction_slug',
        'ro_recommendation',
        'ro_overall_score',
        'ro_optimization_potential',
        'ro_error_message',
        'ro_evaluation_json',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        (
            'Label',
            {
                'description': mark_safe(
                    '<p>Use <strong>Name</strong> and <strong>Description</strong> to tell test runs apart in the list. '
                    '<strong>Conclusion</strong> is filled from the evaluator’s '
                    '<code>proceed_reasoning</code> when you save a successful evaluation (you can edit it).</p>'
                ),
                'fields': ('name', 'description', 'conclusion'),
            },
        ),
        (
            'Inputs',
            {
                'description': mark_safe(
                    '<p>Set <strong>GEMINI_API_KEY</strong> / <strong>GOOGLE_API_KEY</strong>. '
                    'Model and temperature are taken from the selected <strong>Prompt config</strong> '
                    '(edit under AI Prompt Configurations).</p>'
                    '<p>Use <strong>Get evaluation</strong>—inputs do not need to be saved first.</p>'
                    '<p><strong>Save</strong> persists inputs and the last successful preview.</p>'
                ),
                'fields': ('job_description', 'resume_pdf', 'resume_text', 'prompt_config'),
            },
        ),
        (
            'Last run results',
            {
                'fields': (
                    '_results_header',
                    'ro_succeeded',
                    'ro_gemini_model',
                    'ro_instruction_slug',
                    'ro_recommendation',
                    'ro_overall_score',
                    'ro_optimization_potential',
                    'ro_error_message',
                    'ro_evaluation_json',
                    'created_at',
                    'updated_at',
                ),
            },
        ),
    )

    @staticmethod
    def _ro_span(element_id: str, inner) -> str:
        return format_html('<span id="{}">{}</span>', element_id, inner)

    @staticmethod
    def _empty_dash() -> str:
        return format_html('<span class="resume-eval-empty">—</span>')

    @staticmethod
    def _truncate(text: str, limit: int = 72) -> str:
        text = (text or "").strip().replace("\n", " ")
        if not text:
            return ""
        if len(text) <= limit:
            return text
        return text[: limit - 1] + "…"

    @admin.display(description="Name", ordering="name")
    def display_name(self, obj: ResumeJobEvaluation) -> str:
        label = (obj.name or "").strip()
        return label if label else f"#{obj.pk}"

    @admin.display(description="Description", ordering="description")
    def short_description(self, obj: ResumeJobEvaluation) -> str:
        snippet = self._truncate(obj.description, 60)
        return snippet or "—"

    @admin.display(description="Conclusion", ordering="conclusion")
    def short_conclusion(self, obj: ResumeJobEvaluation) -> str:
        snippet = self._truncate(obj.conclusion, 80)
        return snippet or "—"

    @staticmethod
    def _succeeded_icon(value: bool) -> str:
        if value:
            return format_html(
                '<img src="{}" alt="True">',
                static('admin/img/icon-yes.svg'),
            )
        return format_html(
            '<img src="{}" alt="False">',
            static('admin/img/icon-no.svg'),
        )

    @admin.display(description="Succeeded")
    def ro_succeeded(self, obj: ResumeJobEvaluation) -> str:
        has_run = bool(
            obj.evaluation_json
            or (obj.error_message or '').strip()
            or (obj.raw_response_text or '').strip()
        )
        if not has_run:
            inner = self._empty_dash()
        else:
            inner = self._succeeded_icon(obj.succeeded)
        return self._ro_span('resume-eval-ro-succeeded', inner)

    @admin.display(description="Recommendation")
    def ro_recommendation(self, obj: ResumeJobEvaluation) -> str:
        text = (obj.recommendation or '').strip()
        inner = text if text else self._empty_dash()
        return self._ro_span('resume-eval-ro-recommendation', inner)

    @admin.display(description="Overall score")
    def ro_overall_score(self, obj: ResumeJobEvaluation) -> str:
        if obj.overall_score is None:
            inner = self._empty_dash()
        else:
            inner = str(obj.overall_score)
        return self._ro_span('resume-eval-ro-overall-score', inner)

    @admin.display(description="Optimization potential")
    def ro_optimization_potential(self, obj: ResumeJobEvaluation) -> str:
        if obj.optimization_potential is None:
            inner = self._empty_dash()
        else:
            inner = str(obj.optimization_potential)
        return self._ro_span('resume-eval-ro-optimization-potential', inner)

    @admin.display(description="Gemini model")
    def ro_gemini_model(self, obj: ResumeJobEvaluation) -> str:
        text = (obj.gemini_model or '').strip()
        inner = text if text else self._empty_dash()
        return self._ro_span('resume-eval-ro-gemini-model', inner)

    @admin.display(description="Temperature")
    def ro_temperature(self, obj: ResumeJobEvaluation) -> str:
        if obj.temperature_used is None:
            inner = self._empty_dash()
        else:
            inner = str(obj.temperature_used)
        return self._ro_span('resume-eval-ro-temperature', inner)

    @admin.display(description="Instruction slug")
    def ro_instruction_slug(self, obj: ResumeJobEvaluation) -> str:
        text = (obj.instruction_slug or '').strip()
        inner = text if text else self._empty_dash()
        return self._ro_span('resume-eval-ro-instruction-slug', inner)

    @admin.display(description="Error message")
    def ro_error_message(self, obj: ResumeJobEvaluation) -> str:
        text = (obj.error_message or '').strip()
        if text:
            inner = format_html(
                '<span style="color:#ba2121;white-space:pre-wrap;">{}</span>',
                text[:8000],
            )
        else:
            inner = self._empty_dash()
        return self._ro_span('resume-eval-ro-error-message', inner)

    @admin.display(description="")
    def _results_header(self, obj: ResumeJobEvaluation) -> str:
        if obj.pk and obj.evaluation_json and obj.succeeded:
            return 'Summary fields reflect the last saved run.'
        return mark_safe(
            'Run <strong>Get evaluation</strong> above to fill these fields. '
            'Optionally save results onto this row when done.'
        )

    @admin.display(description="Evaluation JSON")
    def ro_evaluation_json(self, obj: ResumeJobEvaluation) -> str:
        data = obj.evaluation_json
        if not data:
            inner = format_html('<em>No JSON payload yet.</em>')
        else:
            try:
                body = json.dumps(data, indent=2, ensure_ascii=False)
            except (TypeError, ValueError):
                body = repr(data)
            inner = format_html(
                '<pre style="white-space:pre-wrap;font-size:12px;max-height:520px;'
                'overflow:auto;background:#0d1117;color:#e6edf3;padding:14px;'
                'border-radius:6px;margin:0;">{}</pre>',
                body[:200000],
            )
        return self._ro_span('resume-eval-ro-evaluation-json', inner)

    def get_urls(self):
        urls = super().get_urls()
        opts = self.model._meta
        basename = '%s_%s' % (opts.app_label, opts.model_name)
        extra = [
            path(
                'eval-preview/',
                self.admin_site.admin_view(self.evaluate_preview),
                name='%s_evaluate_preview' % basename,
            ),
            path(
                '<path:object_id>/persist-eval/',
                self.admin_site.admin_view(self.persist_evaluation_submit),
                name='%s_persist_evaluation' % basename,
            ),
            path(
                '<path:object_id>/run-evaluation/',
                self.admin_site.admin_view(self.run_evaluation_submit),
                name='%s_run_evaluation' % basename,
            ),
        ]
        return extra + urls

    def evaluate_preview(self, request):
        """POST: Gemini from current textarea values — no Django save required."""
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST', 'OPTIONS'])
        opts = self.model._meta
        if not (
            request.user.has_perm(f'{opts.app_label}.add_{opts.model_name}')
            or request.user.has_perm(f'{opts.app_label}.change_{opts.model_name}')
        ):
            return HttpResponse(
                json.dumps({'success': False, 'error': 'Permission denied'}),
                status=403,
                content_type='application/json',
            )

        jd = (request.POST.get('job_description') or '').strip()
        rt, rt_err = resolve_resume_text_from_admin_request(request)
        if rt_err:
            payload = {'success': False, 'error': rt_err, 'evaluation': None, 'raw_text': None}
            return HttpResponse(json.dumps(payload, cls=DjangoJSONEncoder), status=400, content_type='application/json')
        if not jd or not rt:
            payload = {
                'success': False,
                'error': 'Job description and resume text (or resume PDF) are required.',
                'evaluation': None,
                'raw_text': None,
            }
            return HttpResponse(json.dumps(payload, cls=DjangoJSONEncoder), status=400, content_type='application/json')

        pc = None
        raw_pc = request.POST.get('prompt_config') or ''
        if str(raw_pc).strip().isdigit():
            pc = resolve_prompt_config(int(raw_pc))
        if pc is None:
            pc = get_default_prompt_config()
        if pc is None:
            payload = {
                'success': False,
                'error': (
                    "No active prompt for slug resume_job_evaluation. Run "
                    "python manage.py setup_resume_job_evaluation"
                ),
                'evaluation': None,
                'raw_text': None,
            }
            return HttpResponse(json.dumps(payload, cls=DjangoJSONEncoder), status=400, content_type='application/json')

        try:
            result = evaluate_resume_against_job(
                jd,
                rt,
                prompt_config=pc,
            )
            return HttpResponse(json.dumps(result, cls=DjangoJSONEncoder), content_type='application/json')
        except Exception as exc:  # noqa: BLE001
            payload = {'success': False, 'evaluation': None, 'error': str(exc), 'raw_text': None}
            return HttpResponse(json.dumps(payload, cls=DjangoJSONEncoder), status=500, content_type='application/json')

    def persist_evaluation_submit(self, request, object_id):
        """POST JSON body `{"result": <evaluate_resume_against_job-shaped dict>}`."""
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST', 'OPTIONS'])
        obj = get_object_or_404(ResumeJobEvaluation, pk=object_id)
        if not self.has_change_permission(request, obj):
            return HttpResponseForbidden('Change permission denied.')
        try:
            body = json.loads(request.body.decode() or '{}')
        except json.JSONDecodeError:
            return HttpResponse(
                json.dumps({'ok': False, 'error': 'Invalid JSON body'}),
                status=400,
                content_type='application/json',
            )
        result = body.get('result')
        if not isinstance(result, dict) or result.get('success') is not True:
            return HttpResponse(
                json.dumps({'ok': False, 'error': 'Provide result.success=true from Get evaluation'}),
                status=400,
                content_type='application/json',
            )

        gemini_mid = str(
            result.get('gemini_model')
            or getattr(settings, 'GEMINI_RESUME_JOB_EVAL_MODEL', 'gemini-2.5-flash')
        ).strip()
        rpc = resolve_prompt_config(result.get('prompt_config_id'))
        pc = rpc or obj.prompt_config or get_default_prompt_config()

        try:
            persist_resume_job_evaluation_result(
                pk=obj.pk,
                result=result,
                prompt_config=pc,
                fallback_gemini_model_id=gemini_mid,
            )
        except Exception as exc:  # noqa: BLE001
            return HttpResponse(
                json.dumps({'ok': False, 'error': str(exc)}),
                status=400,
                content_type='application/json',
            )

        return HttpResponse(json.dumps({'ok': True}), content_type='application/json')

    def run_evaluation_submit(self, request, object_id):
        """POST only: invoke Gemini against the saved row (prompt-testing loop)."""
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST', 'OPTIONS'])
        obj = get_object_or_404(ResumeJobEvaluation, pk=object_id)
        if not self.has_change_permission(request, obj):
            return HttpResponseForbidden('Change permission denied.')
        pc = obj.prompt_config or get_default_prompt_config()
        if pc is None:
            messages.error(
                request,
                'No active prompt for slug resume_job_evaluation. Run '
                'python manage.py setup_resume_job_evaluation',
            )
        else:
            result = evaluate_resume_against_job(
                obj.job_description,
                obj.resume_text,
                prompt_config=pc,
            )
            gemini_mid = str(result.get('gemini_model') or 'gemini-2.5-flash').strip()
            persist_resume_job_evaluation_result(
                pk=obj.pk,
                result=result,
                prompt_config=pc,
                fallback_gemini_model_id=gemini_mid,
            )
            if result['success']:
                messages.success(
                    request,
                    'Gemini evaluation finished — reload the page if you ran from legacy button.',
                )
            else:
                messages.error(
                    request,
                    f'Gemini evaluation failed: {result.get("error")}',
                )
        ch = 'admin:%s_%s_change' % (self.opts.app_label, self.opts.model_name)
        return redirect(reverse(ch, args=(object_id,)))

    def _persist_pending_from_form(self, request, obj, form) -> bool:
        raw = form.cleaned_data.get('pending_evaluation_result')
        if raw is None:
            raw = request.POST.get('pending_evaluation_result')
        result = parse_pending_evaluation_result(raw)
        if result is None:
            return False

        gemini_mid = str(
            result.get('gemini_model')
            or getattr(settings, 'GEMINI_RESUME_JOB_EVAL_MODEL', 'gemini-2.5-flash')
        ).strip()
        rpc = resolve_prompt_config(result.get('prompt_config_id'))
        pc = (
            rpc
            or form.cleaned_data.get('prompt_config')
            or obj.prompt_config
            or get_default_prompt_config()
        )
        persist_resume_job_evaluation_result(
            pk=obj.pk,
            result=result,
            prompt_config=pc,
            fallback_gemini_model_id=gemini_mid,
        )
        return True

    def save_model(self, request, obj, form, change):
        pc = form.cleaned_data.get('prompt_config')
        if pc is None:
            pc = get_default_prompt_config()
        obj.prompt_config = pc
        super().save_model(request, obj, form, change)

        persisted_eval = self._persist_pending_from_form(request, obj, form)
        if persisted_eval:
            self.message_user(
                request,
                'Saved inputs and last evaluation results.',
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                'Saved inputs.',
                level=messages.INFO,
            )


@admin.register(WhyShouldIApplyPlayground)
class WhyShouldIApplyPlaygroundAdmin(AdminResumePdfExtractMixin, admin.ModelAdmin):
    """Playground: save = draft inputs; separate button runs Gemini (prompt test cycle)."""

    form = WhyShouldIApplyPlaygroundAdminForm
    change_form_template = "admin/ai_service/whyshouldiapplyplayground/change_form.html"
    add_form_template = "admin/ai_service/whyshouldiapplyplayground/add_form.html"
    list_display = [
        "display_name",
        "short_description",
        "gemini_model",
        "instruction_slug",
        "succeeded",
        "created_at",
    ]
    list_filter = ["succeeded", "instruction_slug", "gemini_model", "created_at"]
    search_fields = [
        "name",
        "description",
        "job_description",
        "answer_text",
    ]
    autocomplete_fields = ["prompt_config"]

    readonly_fields = [
        "_results_header",
        "ro_succeeded",
        "ro_gemini_model",
        "ro_temperature",
        "ro_instruction_slug",
        "ro_error_message",
        "ro_answer_text",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Label",
            {
                "description": mark_safe(
                    "<p>Use <strong>Name</strong> and <strong>Description</strong> to tell test runs apart. "
                    "This generates a plain application answer — not a cover letter.</p>"
                ),
                "fields": ("name", "description"),
            },
        ),
        (
            "Inputs",
            {
                "description": mark_safe(
                    "<p>Set <strong>GEMINI_API_KEY</strong> / <strong>GOOGLE_API_KEY</strong>. "
                    "Model and temperature come from the selected <strong>Prompt config</strong>.</p>"
                    "<p>Use <strong>Get answer</strong> — inputs do not need to be saved first.</p>"
                ),
                "fields": ("job_description", "resume_pdf", "resume_text", "prompt_config"),
            },
        ),
        (
            "Last run results",
            {
                "fields": (
                    "_results_header",
                    "ro_succeeded",
                    "ro_gemini_model",
                    "ro_temperature",
                    "ro_instruction_slug",
                    "ro_error_message",
                    "ro_answer_text",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @staticmethod
    def _ro_span(element_id: str, inner) -> str:
        return format_html('<span id="{}">{}</span>', element_id, inner)

    @staticmethod
    def _empty_dash() -> str:
        return format_html('<span class="why-apply-empty">—</span>')

    @staticmethod
    def _truncate(text: str, limit: int = 72) -> str:
        text = (text or "").strip().replace("\n", " ")
        if not text:
            return ""
        if len(text) <= limit:
            return text
        return text[: limit - 1] + "…"

    @admin.display(description="Name", ordering="name")
    def display_name(self, obj: WhyShouldIApplyPlayground) -> str:
        label = (obj.name or "").strip()
        return label if label else f"#{obj.pk}"

    @admin.display(description="Description", ordering="description")
    def short_description(self, obj: WhyShouldIApplyPlayground) -> str:
        snippet = self._truncate(obj.description, 60)
        return snippet or "—"

    @staticmethod
    def _succeeded_icon(value: bool) -> str:
        if value:
            return format_html(
                '<img src="{}" alt="True">',
                static("admin/img/icon-yes.svg"),
            )
        return format_html(
            '<img src="{}" alt="False">',
            static("admin/img/icon-no.svg"),
        )

    @admin.display(description="Succeeded")
    def ro_succeeded(self, obj: WhyShouldIApplyPlayground) -> str:
        has_run = bool(
            (obj.answer_text or "").strip()
            or (obj.error_message or "").strip()
            or (obj.raw_response_text or "").strip()
        )
        if not has_run:
            inner = self._empty_dash()
        else:
            inner = self._succeeded_icon(obj.succeeded)
        return self._ro_span("why-apply-ro-succeeded", inner)

    @admin.display(description="Gemini model")
    def ro_gemini_model(self, obj: WhyShouldIApplyPlayground) -> str:
        text = (obj.gemini_model or "").strip()
        inner = text if text else self._empty_dash()
        return self._ro_span("why-apply-ro-gemini-model", inner)

    @admin.display(description="Temperature")
    def ro_temperature(self, obj: WhyShouldIApplyPlayground) -> str:
        if obj.temperature_used is None:
            inner = self._empty_dash()
        else:
            inner = str(obj.temperature_used)
        return self._ro_span("why-apply-ro-temperature", inner)

    @admin.display(description="Instruction slug")
    def ro_instruction_slug(self, obj: WhyShouldIApplyPlayground) -> str:
        text = (obj.instruction_slug or "").strip()
        inner = text if text else self._empty_dash()
        return self._ro_span("why-apply-ro-instruction-slug", inner)

    @admin.display(description="Error message")
    def ro_error_message(self, obj: WhyShouldIApplyPlayground) -> str:
        text = (obj.error_message or "").strip()
        if text:
            inner = format_html(
                '<span style="color:#ba2121;white-space:pre-wrap;">{}</span>',
                text[:8000],
            )
        else:
            inner = self._empty_dash()
        return self._ro_span("why-apply-ro-error-message", inner)

    @admin.display(description="")
    def _results_header(self, obj: WhyShouldIApplyPlayground) -> str:
        if obj.pk and (obj.answer_text or "").strip() and obj.succeeded:
            return "Answer below reflects the last saved run."
        return mark_safe(
            'Run <strong>Get answer</strong> above to fill these fields. '
            "Optionally save results onto this row when done."
        )

    @admin.display(description="Answer")
    def ro_answer_text(self, obj: WhyShouldIApplyPlayground) -> str:
        text = (obj.answer_text or "").strip()
        if not text:
            inner = format_html("<em>No answer yet.</em>")
        else:
            inner = format_html(
                '<pre style="white-space:pre-wrap;font-size:13px;max-height:520px;'
                'overflow:auto;background:#f8f9fa;padding:14px;border-radius:6px;margin:0;">{}</pre>',
                text[:65535],
            )
        return self._ro_span("why-apply-ro-answer-text", inner)

    def get_urls(self):
        urls = super().get_urls()
        opts = self.model._meta
        basename = "%s_%s" % (opts.app_label, opts.model_name)
        extra = [
            path(
                "generate-preview/",
                self.admin_site.admin_view(self.generate_preview),
                name="%s_generate_preview" % basename,
            ),
            path(
                "<path:object_id>/persist-generation/",
                self.admin_site.admin_view(self.persist_generation_submit),
                name="%s_persist_generation" % basename,
            ),
            path(
                "<path:object_id>/run-generation/",
                self.admin_site.admin_view(self.run_generation_submit),
                name="%s_run_generation" % basename,
            ),
        ]
        return extra + urls

    def generate_preview(self, request):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST", "OPTIONS"])
        opts = self.model._meta
        if not (
            request.user.has_perm(f"{opts.app_label}.add_{opts.model_name}")
            or request.user.has_perm(f"{opts.app_label}.change_{opts.model_name}")
        ):
            return HttpResponse(
                json.dumps({"success": False, "error": "Permission denied"}),
                status=403,
                content_type="application/json",
            )

        jd = (request.POST.get("job_description") or "").strip()
        rt, rt_err = resolve_resume_text_from_admin_request(request)
        if rt_err:
            payload = {"success": False, "error": rt_err, "answer_text": "", "raw_text": None}
            return HttpResponse(
                json.dumps(payload, cls=DjangoJSONEncoder),
                status=400,
                content_type="application/json",
            )
        if not jd or not rt:
            payload = {
                "success": False,
                "error": "Job description and resume text (or resume PDF) are required.",
                "answer_text": "",
                "raw_text": None,
            }
            return HttpResponse(
                json.dumps(payload, cls=DjangoJSONEncoder),
                status=400,
                content_type="application/json",
            )

        pc = None
        raw_pc = request.POST.get("prompt_config") or ""
        if str(raw_pc).strip().isdigit():
            pc = resolve_why_apply_prompt_config(int(raw_pc))
        if pc is None:
            pc = get_why_apply_default_prompt_config()
        if pc is None:
            payload = {
                "success": False,
                "error": (
                    f"No active prompt for slug {WHY_SHOULD_I_APPLY_SERVICE_SLUG}. Run "
                    "python manage.py setup_why_should_i_apply"
                ),
                "answer_text": "",
                "raw_text": None,
            }
            return HttpResponse(
                json.dumps(payload, cls=DjangoJSONEncoder),
                status=400,
                content_type="application/json",
            )

        try:
            result = generate_why_should_i_apply(jd, rt, prompt_config=pc)
            return HttpResponse(
                json.dumps(result, cls=DjangoJSONEncoder),
                content_type="application/json",
            )
        except Exception as exc:  # noqa: BLE001
            payload = {
                "success": False,
                "answer_text": "",
                "error": str(exc),
                "raw_text": None,
            }
            return HttpResponse(
                json.dumps(payload, cls=DjangoJSONEncoder),
                status=500,
                content_type="application/json",
            )

    def persist_generation_submit(self, request, object_id):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST", "OPTIONS"])
        obj = get_object_or_404(WhyShouldIApplyPlayground, pk=object_id)
        if not self.has_change_permission(request, obj):
            return HttpResponseForbidden("Change permission denied.")
        try:
            body = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return HttpResponse(
                json.dumps({"ok": False, "error": "Invalid JSON body"}),
                status=400,
                content_type="application/json",
            )
        result = body.get("result")
        if not isinstance(result, dict) or result.get("success") is not True:
            return HttpResponse(
                json.dumps({"ok": False, "error": "Provide result.success=true from Get answer"}),
                status=400,
                content_type="application/json",
            )

        gemini_mid = str(
            result.get("gemini_model")
            or getattr(settings, "GEMINI_RESUME_JOB_EVAL_MODEL", "gemini-2.5-flash")
        ).strip()
        rpc = resolve_why_apply_prompt_config(result.get("prompt_config_id"))
        pc = rpc or obj.prompt_config or get_why_apply_default_prompt_config()

        try:
            persist_why_should_i_apply_result(
                pk=obj.pk,
                result=result,
                prompt_config=pc,
                fallback_gemini_model_id=gemini_mid,
            )
        except Exception as exc:  # noqa: BLE001
            return HttpResponse(
                json.dumps({"ok": False, "error": str(exc)}),
                status=400,
                content_type="application/json",
            )

        return HttpResponse(json.dumps({"ok": True}), content_type="application/json")

    def run_generation_submit(self, request, object_id):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST", "OPTIONS"])
        obj = get_object_or_404(WhyShouldIApplyPlayground, pk=object_id)
        if not self.has_change_permission(request, obj):
            return HttpResponseForbidden("Change permission denied.")
        pc = obj.prompt_config or get_why_apply_default_prompt_config()
        if pc is None:
            messages.error(
                request,
                f"No active prompt for slug {WHY_SHOULD_I_APPLY_SERVICE_SLUG}. Run "
                "python manage.py setup_why_should_i_apply",
            )
        else:
            result = generate_why_should_i_apply(
                obj.job_description,
                obj.resume_text,
                prompt_config=pc,
            )
            gemini_mid = str(result.get("gemini_model") or "gemini-2.5-flash").strip()
            persist_why_should_i_apply_result(
                pk=obj.pk,
                result=result,
                prompt_config=pc,
                fallback_gemini_model_id=gemini_mid,
            )
            if result["success"]:
                messages.success(request, "Gemini generation finished.")
            else:
                messages.error(
                    request,
                    f'Gemini generation failed: {result.get("error")}',
                )
        ch = "admin:%s_%s_change" % (self.opts.app_label, self.opts.model_name)
        return redirect(reverse(ch, args=(object_id,)))

    def _persist_pending_from_form(self, request, obj, form) -> bool:
        raw = form.cleaned_data.get("pending_generation_result")
        if raw is None:
            raw = request.POST.get("pending_generation_result")
        result = parse_pending_generation_result(raw)
        if result is None:
            return False

        gemini_mid = str(
            result.get("gemini_model")
            or getattr(settings, "GEMINI_RESUME_JOB_EVAL_MODEL", "gemini-2.5-flash")
        ).strip()
        rpc = resolve_why_apply_prompt_config(result.get("prompt_config_id"))
        pc = (
            rpc
            or form.cleaned_data.get("prompt_config")
            or obj.prompt_config
            or get_why_apply_default_prompt_config()
        )
        persist_why_should_i_apply_result(
            pk=obj.pk,
            result=result,
            prompt_config=pc,
            fallback_gemini_model_id=gemini_mid,
        )
        return True

    def save_model(self, request, obj, form, change):
        pc = form.cleaned_data.get("prompt_config")
        if pc is None:
            pc = get_why_apply_default_prompt_config()
        obj.prompt_config = pc
        super().save_model(request, obj, form, change)

        persisted = self._persist_pending_from_form(request, obj, form)
        if persisted:
            self.message_user(
                request,
                "Saved inputs and last generation results.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(request, "Saved inputs.", level=messages.INFO)
