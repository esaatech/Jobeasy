from django import forms

from .models import AIService, AIPromptConfiguration, ResumeJobEvaluation, WhyShouldIApplyPlayground
from .resume_job_evaluation import RESUME_JOB_EVALUATION_SERVICE_SLUG
from .why_should_i_apply import WHY_SHOULD_I_APPLY_SERVICE_SLUG

RESUME_PDF_FIELD_HELP = (
    "Optional. Upload a PDF and use “Load PDF into resume text” to fill the textarea "
    "(same extractor as dashboard resume upload). You can also attach a PDF when running "
    "Get evaluation / Get answer without loading first."
)


class ResumeJobEvaluationAdminForm(forms.ModelForm):
    """Saved rows keep job/resume/prompt FK; Gemini runs inline via Get evaluation."""

    pending_evaluation_result = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    resume_pdf = forms.FileField(
        required=False,
        label="Resume PDF",
        help_text=RESUME_PDF_FIELD_HELP,
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf"}),
    )

    class Meta:
        model = ResumeJobEvaluation
        fields = (
            "name",
            "description",
            "conclusion",
            "job_description",
            "resume_pdf",
            "resume_text",
            "prompt_config",
        )
        widgets = {
            "name": forms.TextInput(attrs={"size": 80}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "conclusion": forms.Textarea(attrs={"rows": 3}),
            "job_description": forms.Textarea(attrs={"rows": 8}),
            "resume_text": forms.Textarea(attrs={"rows": 12}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        svc = AIService.objects.filter(
            slug=RESUME_JOB_EVALUATION_SERVICE_SLUG, is_active=True
        ).first()
        qs = AIPromptConfiguration.objects.none()
        if svc:
            qs = svc.prompts.filter(is_active=True)
        self.fields["prompt_config"].queryset = qs
        self.fields["prompt_config"].required = False
        self.fields["prompt_config"].help_text = (
            "Uses the service default if left empty when you run Gemini. Set model and temperature "
            "on each prompt under AI Prompt Configurations (slug resume_job_evaluation)."
        )


class WhyShouldIApplyPlaygroundAdminForm(forms.ModelForm):
    """Saved rows keep job/resume/prompt FK; Gemini runs inline via Get answer."""

    pending_generation_result = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    resume_pdf = forms.FileField(
        required=False,
        label="Resume PDF",
        help_text=RESUME_PDF_FIELD_HELP,
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf"}),
    )

    class Meta:
        model = WhyShouldIApplyPlayground
        fields = (
            "name",
            "description",
            "job_description",
            "resume_pdf",
            "resume_text",
            "prompt_config",
        )
        widgets = {
            "name": forms.TextInput(attrs={"size": 80}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "job_description": forms.Textarea(attrs={"rows": 8}),
            "resume_text": forms.Textarea(attrs={"rows": 12}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        svc = AIService.objects.filter(
            slug=WHY_SHOULD_I_APPLY_SERVICE_SLUG, is_active=True
        ).first()
        qs = AIPromptConfiguration.objects.none()
        if svc:
            qs = svc.prompts.filter(is_active=True)
        self.fields["prompt_config"].queryset = qs
        self.fields["prompt_config"].required = False
        self.fields["prompt_config"].help_text = (
            "Uses the service default if left empty when you run Gemini. Set model and temperature "
            "on each prompt under AI Prompt Configurations (slug why_should_i_apply)."
        )
