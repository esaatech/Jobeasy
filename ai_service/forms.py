from django import forms

from .models import AIService, AIPromptConfiguration, ResumeJobEvaluation
from .resume_job_evaluation import RESUME_JOB_EVALUATION_SERVICE_SLUG


class ResumeJobEvaluationAdminForm(forms.ModelForm):
    """Saved rows keep job/resume/prompt FK; Gemini runs inline via Get evaluation."""

    pending_evaluation_result = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = ResumeJobEvaluation
        fields = (
            "name",
            "description",
            "conclusion",
            "job_description",
            "resume_text",
            "prompt_config",
        )
        widgets = {
            "name": forms.TextInput(attrs={"size": 80}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "conclusion": forms.Textarea(attrs={"rows": 3}),
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
