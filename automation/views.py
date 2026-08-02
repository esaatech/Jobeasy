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
        'search_purpose_choices': UltimateAutomationProfile.SEARCH_PURPOSE_CHOICES,
        'work_arrangement_choices': [
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
            ('onsite', 'On-site'),
        ],
        'setup_ui_version': 'prefs-v4-locations-api',
        'locations_countries_url': reverse('automation:locations_countries'),
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


VALID_WORK_ARRANGEMENTS = {'remote', 'hybrid', 'onsite'}
VALID_SEARCH_PURPOSES = {c[0] for c in UltimateAutomationProfile.SEARCH_PURPOSE_CHOICES}


def _parse_json_list(raw):
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _parse_work_arrangements(raw) -> list[str]:
    items = _parse_json_list(raw)
    if not items and isinstance(raw, str) and raw.strip() and not raw.strip().startswith('['):
        items = [p.strip() for p in raw.split(',') if p.strip()]
    seen = set()
    out = []
    for item in items:
        key = str(item or '').strip().lower()
        if key in VALID_WORK_ARRANGEMENTS and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def _parse_countries(raw) -> list[dict]:
    items = _parse_json_list(raw)
    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get('name') or '').strip()[:100]
        cca2 = str(item.get('cca2') or '').strip().upper()[:3]
        if not name or not cca2:
            continue
        states_raw = item.get('states') or []
        if isinstance(states_raw, str):
            states = [s.strip() for s in states_raw.split(',') if s.strip()]
        elif isinstance(states_raw, list):
            states = [str(s).strip() for s in states_raw if str(s).strip()]
        else:
            states = []
        cleaned.append({'name': name, 'cca2': cca2, 'states': states[:50]})
    return cleaned[:20]


@login_required
@require_http_methods(['GET', 'POST'])
def ultimate_setup(request):
    """Enroll-first: titles (step 1) then location/prefs (step 2). Ultimate unlocks apply."""
    profile, _ = UltimateAutomationProfile.objects.get_or_create(user=request.user)
    resumes = Resume.objects.filter(user=request.user).order_by('-updated_at')
    is_ultimate = _is_ultimate_subscriber(request.user)

    if request.method == 'POST':
        primary = _parse_title_list(request.POST.get('primary_titles'))
        related = _parse_title_list(request.POST.get('related_titles'))
        exclude = _parse_title_list(request.POST.get('exclude_titles'))
        resume_id = request.POST.get('default_resume') or None
        enable_auto_apply = request.POST.get('auto_apply_enabled') == 'on'
        search_purpose = (request.POST.get('search_purpose') or '').strip()
        other_purpose = (request.POST.get('other_purpose') or '').strip()[:500]
        countries = _parse_countries(request.POST.get('preferred_countries'))
        city = (request.POST.get('city') or '').strip()[:100]
        work_arrangements = _parse_work_arrangements(request.POST.get('work_arrangements'))

        try:
            distance_miles = int(request.POST.get('distance_miles') or 50)
        except (TypeError, ValueError):
            distance_miles = 50
        distance_miles = max(0, min(distance_miles, 500))

        error = None
        if not primary:
            error = 'Add at least one primary title before continuing.'
        elif search_purpose not in VALID_SEARCH_PURPOSES:
            error = 'Choose why you are looking for a job.'
        elif search_purpose == 'other' and not other_purpose:
            error = 'Please specify your reason when selecting Other.'
        elif not work_arrangements:
            error = 'Select at least one work arrangement (remote, hybrid, or on-site).'
        elif not city and not countries:
            error = 'Add a city or at least one country where you want to work.'

        if error:
            return render(
                request,
                'automation/ultimate_setup.html',
                _setup_context(request.user, profile, resumes, error=error),
            )

        profile.primary_titles = primary
        profile.related_titles = related
        profile.exclude_titles = exclude
        profile.search_purpose = search_purpose
        profile.other_purpose = other_purpose if search_purpose == 'other' else ''
        profile.preferred_countries = countries
        profile.city = city
        profile.distance_miles = distance_miles
        profile.work_arrangements = work_arrangements
        # max_applications_per_day is admin-managed; do not overwrite from setup form
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


@require_http_methods(['GET'])
def locations_countries(request):
    """Return supported countries for job-search preferences (US, CA, GB to start)."""
    from .data.locations import list_countries

    return JsonResponse({'countries': list_countries()})


@require_http_methods(['GET'])
def locations_regions(request, code: str):
    """Return states / provinces / nations for a supported country code."""
    from .data.locations import get_country, list_regions

    country = get_country(code)
    regions = list_regions(code)
    if country is None or regions is None:
        return JsonResponse({'error': 'Unknown country code.'}, status=404)

    return JsonResponse({
        'code': country['code'],
        'name': country['name'],
        'region_label': country['region_label'],
        'regions': regions,
    })
