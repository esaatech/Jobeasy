import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from resume_builder.models import Resume
from subscriptions.models import UserSubscription

from .models import FREE_TITLE_FAMILY_AI_GENERATIONS, UltimateAutomationProfile
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
    if sub and sub.is_active:
        return True
    # Test plan mirrors Ultimate for local/QA.
    test_sub = (
        UserSubscription.objects.filter(
            user=user,
            plan__name__iexact='Test',
            status='ACTIVE',
        )
        .select_related('plan')
        .first()
    )
    return bool(test_sub and test_sub.is_active)


def _setup_context(user, profile, resumes, error=None):
    is_ultimate = _is_ultimate_subscriber(user)
    used = profile.title_family_ai_generations or 0
    remaining = None if is_ultimate else max(0, FREE_TITLE_FAMILY_AI_GENERATIONS - used)
    ctx = {
        'profile': profile,
        'resumes': resumes,
        'is_ultimate': is_ultimate,
        'free_generation_limit': FREE_TITLE_FAMILY_AI_GENERATIONS,
        'free_generations_remaining': remaining,
        'can_generate_titles': is_ultimate or (remaining is not None and remaining > 0),
        'ultimate_pricing_url': f"{reverse('subscriptions:pricing')}?plan=ultimate",
    }
    if error:
        ctx['error'] = error
    return ctx


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
    """Enroll-first: any logged-in user can build a title family; Ultimate unlocks apply."""
    profile, _ = UltimateAutomationProfile.objects.get_or_create(user=request.user)
    resumes = Resume.objects.filter(user=request.user).order_by('-updated_at')
    is_ultimate = _is_ultimate_subscriber(request.user)

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
                _setup_context(
                    request.user,
                    profile,
                    resumes,
                    error='Add at least one primary title before continuing.',
                ),
            )

        profile.primary_titles = primary
        profile.related_titles = related
        profile.exclude_titles = exclude
        # Matching/apply only for Ultimate; free users save a draft profile.
        profile.auto_apply_enabled = bool(is_ultimate and enable_auto_apply and primary)

        if resume_id:
            resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
            profile.default_resume = resume
        else:
            profile.default_resume = resumes.first()

        profile.save()
        profile.mark_title_family_confirmed()
        return redirect('automation:ultimate_setup_done')

    return render(
        request,
        'automation/ultimate_setup.html',
        _setup_context(request.user, profile, resumes),
    )


@login_required
def ultimate_setup_done(request):
    profile = get_object_or_404(UltimateAutomationProfile, user=request.user)
    is_ultimate = _is_ultimate_subscriber(request.user)
    return render(
        request,
        'automation/ultimate_setup_done.html',
        {
            'profile': profile,
            'is_ultimate': is_ultimate,
            'ultimate_pricing_url': f"{reverse('subscriptions:pricing')}?plan=ultimate",
        },
    )


@login_required
@require_POST
def suggest_title_family(request):
    """AI-suggest title family from selected resume (JSON). Free users: limited generates."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}

    profile, _ = UltimateAutomationProfile.objects.get_or_create(user=request.user)
    is_ultimate = _is_ultimate_subscriber(request.user)
    used = profile.title_family_ai_generations or 0

    if not is_ultimate and used >= FREE_TITLE_FAMILY_AI_GENERATIONS:
        return JsonResponse(
            {
                'error': (
                    f'Free limit reached ({FREE_TITLE_FAMILY_AI_GENERATIONS} AI suggestions). '
                    'Edit titles manually or upgrade to Ultimate for more.'
                ),
                'free_generations_remaining': 0,
                'upgrade_url': f"{reverse('subscriptions:pricing')}?plan=ultimate",
            },
            status=403,
        )

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

    profile.primary_titles = suggestions['primary_titles']
    profile.related_titles = suggestions['related_titles']
    profile.exclude_titles = suggestions['exclude_titles']
    profile.default_resume = resume
    profile.title_family_confirmed = False
    profile.title_family_ai_generations = used + 1
    profile.save(
        update_fields=[
            'primary_titles',
            'related_titles',
            'exclude_titles',
            'default_resume',
            'title_family_confirmed',
            'title_family_ai_generations',
            'updated_at',
        ]
    )

    remaining = None if is_ultimate else max(
        0, FREE_TITLE_FAMILY_AI_GENERATIONS - profile.title_family_ai_generations
    )

    return JsonResponse({
        'ok': True,
        'resume_id': resume.pk,
        **suggestions,
        'free_generations_remaining': remaining,
        'next': reverse('automation:ultimate_setup'),
    })
