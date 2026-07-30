import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from resume_builder.models import Resume
from subscriptions.models import UserSubscription

from .models import UltimateAutomationProfile
from .services.title_family import generate_title_family_from_resume

logger = logging.getLogger(__name__)


def _is_ultimate_subscriber(user) -> bool:
    sub = (
        UserSubscription.objects.filter(
            user=user,
            plan__name__iexact='Ultimate',
            status='ACTIVE',
        )
        .select_related('plan')
        .first()
    )
    return bool(sub and sub.is_active)


def _parse_title_list(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            items = parsed if isinstance(parsed, list) else [t.strip() for t in text.split(',') if t.strip()]
        except json.JSONDecodeError:
            items = [t.strip() for t in text.replace('\n', ',').split(',') if t.strip()]
    else:
        return []

    seen = set()
    out = []
    for item in items:
        title = str(item or '').strip()
        key = title.lower()
        if title and key not in seen:
            seen.add(key)
            out.append(title[:120])
    return out


@login_required
@require_http_methods(['GET', 'POST'])
def ultimate_setup(request):
    """Ultimate onboarding: confirm title family before auto-apply."""
    if not _is_ultimate_subscriber(request.user):
        return redirect('subscriptions:pricing')

    profile, _ = UltimateAutomationProfile.objects.get_or_create(user=request.user)
    resumes = Resume.objects.filter(user=request.user).order_by('-updated_at')

    if request.method == 'POST':
        primary = _parse_title_list(request.POST.get('primary_titles'))
        related = _parse_title_list(request.POST.get('related_titles'))
        exclude = _parse_title_list(request.POST.get('exclude_titles'))
        resume_id = request.POST.get('default_resume') or None
        enable_auto_apply = request.POST.get('auto_apply_enabled') == 'on'

        if not primary:
            return render(
                request,
                'automation/ultimate_setup.html',
                {
                    'profile': profile,
                    'resumes': resumes,
                    'error': 'Add at least one primary title before continuing.',
                },
            )

        profile.primary_titles = primary
        profile.related_titles = related
        profile.exclude_titles = exclude
        profile.auto_apply_enabled = enable_auto_apply and bool(primary)

        if resume_id:
            resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
            profile.default_resume = resume
        else:
            profile.default_resume = resumes.first()

        profile.mark_title_family_confirmed()
        profile.save()
        return redirect('automation:ultimate_setup_done')

    return render(
        request,
        'automation/ultimate_setup.html',
        {
            'profile': profile,
            'resumes': resumes,
        },
    )


@login_required
def ultimate_setup_done(request):
    if not _is_ultimate_subscriber(request.user):
        return redirect('subscriptions:pricing')
    profile = get_object_or_404(UltimateAutomationProfile, user=request.user)
    return render(request, 'automation/ultimate_setup_done.html', {'profile': profile})


@login_required
@require_POST
def suggest_title_family(request):
    """AI-suggest title family from selected resume (JSON)."""
    if not _is_ultimate_subscriber(request.user):
        return JsonResponse({'error': 'Ultimate plan required.'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}

    resume_id = payload.get('resume_id')
    resume = None
    if resume_id:
        resume = Resume.objects.filter(pk=resume_id, user=request.user).first()
    if resume is None:
        resume = Resume.objects.filter(user=request.user).order_by('-updated_at').first()
    if resume is None:
        return JsonResponse({'error': 'Create a resume first, then generate titles.'}, status=400)

    try:
        suggestions = generate_title_family_from_resume(resume)
    except Exception as exc:
        logger.exception('Title family generation failed for user %s', request.user.pk)
        return JsonResponse({'error': str(exc)}, status=500)

    profile, _ = UltimateAutomationProfile.objects.get_or_create(user=request.user)
    # Prefill only; user must still confirm via setup form.
    profile.primary_titles = suggestions['primary_titles']
    profile.related_titles = suggestions['related_titles']
    profile.exclude_titles = suggestions['exclude_titles']
    profile.default_resume = resume
    profile.title_family_confirmed = False
    profile.save(
        update_fields=[
            'primary_titles',
            'related_titles',
            'exclude_titles',
            'default_resume',
            'title_family_confirmed',
            'updated_at',
        ]
    )

    return JsonResponse({
        'ok': True,
        'resume_id': resume.pk,
        **suggestions,
        'next': reverse('automation:ultimate_setup'),
    })
