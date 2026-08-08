from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import MatchedTask, StaffMatchRunPreferences, UltimateAutomationProfile
from .services.apply_tasks import complete_matched_task, skip_matched_task
from .services.application_builder import build_packets_for_tasks
from .services.job_matcher import (
    profile_is_match_ready,
    run_match_cycle,
    ultimate_subscriber_user_ids,
)


class MatchedTaskQueueFilter(admin.SimpleListFilter):
    title = 'queue'
    parameter_name = 'queue'

    def lookups(self, request, model_admin):
        return [
            ('open', 'Open (ready + fit paused)'),
            ('ready', 'Ready to apply'),
            ('fit_paused', 'Fit paused'),
            ('matched', 'Matched (pre-fit)'),
            ('done', 'Applied / skipped'),
            ('all', 'All statuses'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'open':
            return queryset.filter(
                status__in=[MatchedTask.STATUS_READY, MatchedTask.STATUS_FIT_PAUSED]
            )
        if value == 'ready':
            return queryset.filter(status=MatchedTask.STATUS_READY)
        if value == 'fit_paused':
            return queryset.filter(status=MatchedTask.STATUS_FIT_PAUSED)
        if value == 'matched':
            return queryset.filter(status=MatchedTask.STATUS_MATCHED)
        if value == 'done':
            return queryset.filter(
                status__in=[MatchedTask.STATUS_APPLIED, MatchedTask.STATUS_SKIPPED]
            )
        return queryset


@admin.register(UltimateAutomationProfile)
class UltimateAutomationProfileAdmin(admin.ModelAdmin):
    change_list_template = 'admin/automation/ultimateautomationprofile/change_list.html'
    list_display = [
        'user',
        'auto_apply_enabled',
        'title_family_confirmed',
        'city',
        'max_applications_per_day',
        'setup_completed',
        'updated_at',
    ]
    list_filter = ['auto_apply_enabled', 'title_family_confirmed', 'setup_completed', 'search_purpose']
    search_fields = ['user__username', 'user__email', 'city']
    readonly_fields = [
        'created_at',
        'updated_at',
        'title_family_confirmed_at',
        'title_family_ai_generations',
    ]
    raw_id_fields = ['default_resume']
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'primary_titles',
                'related_titles',
                'exclude_titles',
                'default_resume',
                'auto_apply_enabled',
                'max_applications_per_day',
            )
        }),
        ('Search preferences', {
            'fields': (
                'search_purpose',
                'other_purpose',
                'preferred_countries',
                'city',
                'distance_miles',
                'work_arrangements',
            )
        }),
        ('Status', {
            'fields': (
                'title_family_confirmed',
                'title_family_confirmed_at',
                'title_family_ai_generations',
                'setup_completed',
                'created_at',
                'updated_at',
            )
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'match-ultimate-users/',
                self.admin_site.admin_view(self.match_ultimate_users_view),
                name='automation_ultimateautomationprofile_match',
            ),
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['match_ultimate_url'] = reverse(
            'admin:automation_ultimateautomationprofile_match'
        )
        return super().changelist_view(request, extra_context=extra_context)

    def match_ultimate_users_view(self, request):
        if not self.has_change_permission(request):
            messages.error(request, 'You do not have permission to match Ultimate users.')
            return redirect('admin:automation_ultimateautomationprofile_changelist')

        prefs, _ = StaffMatchRunPreferences.objects.get_or_create(user=request.user)

        if request.method == 'POST' and request.POST.get('run_match'):
            raw_ids = request.POST.getlist('user_ids')
            user_ids = []
            for value in raw_ids:
                try:
                    user_ids.append(int(value))
                except (TypeError, ValueError):
                    continue

            allowed = set(ultimate_subscriber_user_ids())
            user_ids = [uid for uid in user_ids if uid in allowed]

            optimize_resume = request.POST.get('optimize_resume') == '1'
            generate_cover_letter = request.POST.get('generate_cover_letter') == '1'
            generate_why_should_hire = request.POST.get('generate_why_should_hire') == '1'
            remember = request.POST.get('remember_prefs') == '1'

            if remember:
                prefs.optimize_resume = optimize_resume
                prefs.generate_cover_letter = generate_cover_letter
                prefs.generate_why_should_hire = generate_why_should_hire
                prefs.save()

            if not user_ids:
                messages.warning(request, 'No Ultimate/Test users selected.')
                return redirect('admin:automation_ultimateautomationprofile_match')

            User = get_user_model()
            for user in User.objects.filter(pk__in=user_ids):
                UltimateAutomationProfile.objects.get_or_create(user=user)

            result = run_match_cycle(user_ids=user_ids)
            tasks_url = reverse('admin:automation_matchedtask_changelist')
            messages.success(
                request,
                format_html(
                    'Match complete for {} user(s): '
                    'created {} new MatchedTask(s) '
                    '(existing user+job pairs skipped). '
                    '<a href="{}">View matched tasks</a>',
                    result.users_considered,
                    result.tasks_created,
                    tasks_url,
                ),
            )
            for user_result in result.per_user:
                if user_result.skipped_ineligible:
                    messages.info(
                        request,
                        f'{user_result.username}: skipped ({user_result.reason})',
                    )
                elif user_result.skipped_cap:
                    messages.info(
                        request,
                        f'{user_result.username}: daily cap reached',
                    )
                elif user_result.created:
                    messages.info(
                        request,
                        f'{user_result.username}: created {user_result.created} task(s)',
                    )

            if result.created_tasks:
                packet_results = build_packets_for_tasks(
                    result.created_tasks,
                    optimize_resume=optimize_resume,
                    generate_cover_letter=generate_cover_letter,
                    generate_why_should_hire=generate_why_should_hire,
                )
                ready = sum(1 for r in packet_results if r.status == MatchedTask.STATUS_READY)
                paused = sum(
                    1 for r in packet_results if r.status == MatchedTask.STATUS_FIT_PAUSED
                )
                eager = optimize_resume or generate_cover_letter or generate_why_should_hire
                messages.info(
                    request,
                    f'Fit complete: {ready} ready, {paused} fit-paused '
                    f'(same JobFitGateSettings as dashboard'
                    f'{"; eager packets for checked options" if eager else ""}).',
                )

            return redirect('admin:automation_matchedtask_changelist')

        rows = []
        User = get_user_model()
        for user in User.objects.filter(pk__in=ultimate_subscriber_user_ids()).order_by('username'):
            profile, _ = UltimateAutomationProfile.objects.get_or_create(user=user)
            ready, reason = profile_is_match_ready(profile)
            plan = (
                user.usersubscription_set.filter(status='ACTIVE')
                .select_related('plan')
                .order_by('-created_at')
                .first()
            )
            titles = profile.title_family[:3]
            rows.append({
                'user': user,
                'profile': profile,
                'ready': ready,
                'reason': reason or '',
                'plan_name': plan.plan.name if plan else '—',
                'title_preview': ', '.join(titles) if titles else '',
            })

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Match Ultimate users',
            'rows': rows,
            'prefs': prefs,
        }
        return render(request, 'admin/automation/match_ultimate_users.html', context)


@admin.register(MatchedTask)
class MatchedTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'ops_open_link',
        'user',
        'job_title',
        'company',
        'job_location',
        'work_arrangement',
        'fit_score_display',
        'fit_recommendation',
        'status',
        'application_link',
        'resume_link',
        'created_at',
        'applied_at',
    ]
    list_filter = [
        MatchedTaskQueueFilter,
        'status',
        'fit_tier',
        'skip_reason',
        'job__work_arrangement',
        'created_at',
    ]
    search_fields = [
        'user__username',
        'user__email',
        'job__title',
        'job__company',
        'application_url',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'applied_at',
        'fit_summary',
        'fit_tier',
        'fit_score',
    ]
    raw_id_fields = [
        'user',
        'job',
        'fit_evaluation',
        'source_resume',
        'optimized_resume',
        'cover_letter',
        'why_should_i_apply_answer',
    ]
    ordering = ['-fit_score', '-created_at']
    list_select_related = ['user', 'job', 'optimized_resume', 'source_resume']
    actions = [
        'mark_as_applied',
        'mark_skipped_captcha',
        'mark_skipped_login_required',
        'mark_skipped_job_closed',
        'mark_skipped_geo_block',
        'mark_skipped_other',
    ]

    fieldsets = (
        (None, {
            'fields': ('user', 'job', 'application_url', 'status'),
        }),
        ('Fit evaluation', {
            'fields': ('fit_score', 'fit_tier', 'fit_evaluation', 'fit_summary'),
        }),
        ('Apply packet', {
            'fields': (
                'source_resume',
                'optimized_resume',
                'cover_letter',
                'why_should_i_apply_answer',
            ),
        }),
        ('Operator', {
            'fields': ('skip_reason', 'operator_notes', 'applied_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user',
            'job',
            'optimized_resume',
            'source_resume',
            'cover_letter',
        )

    def changelist_view(self, request, extra_context=None):
        if (
            request.method == 'GET'
            and 'queue' not in request.GET
            and 'status__exact' not in request.GET
            and 'status__in' not in request.GET
        ):
            params = request.GET.copy()
            params['queue'] = 'open'
            return HttpResponseRedirect(f'{request.path}?{params.urlencode()}')
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description='Open')
    def ops_open_link(self, obj):
        url = reverse('automation:matched_task_ops', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Open</a>',
            url,
        )

    @admin.display(description='Job title', ordering='job__title')
    def job_title(self, obj):
        return obj.job.title if obj.job_id else '—'

    @admin.display(description='Company', ordering='job__company')
    def company(self, obj):
        return obj.job.company if obj.job_id else '—'

    @admin.display(description='Location', ordering='job__location')
    def job_location(self, obj):
        return obj.job.location if obj.job_id else '—'

    @admin.display(description='Workplace', ordering='job__work_arrangement')
    def work_arrangement(self, obj):
        if not obj.job_id:
            return '—'
        return obj.job.get_work_arrangement_display()

    @admin.display(description='Fit score', ordering='fit_score')
    def fit_score_display(self, obj):
        if obj.fit_score is not None:
            return obj.fit_score
        summary = obj.fit_summary or {}
        score = summary.get('overall_score')
        return score if score is not None else '—'

    @admin.display(description='Fit')
    def fit_recommendation(self, obj):
        summary = obj.fit_summary or {}
        if summary.get('error') and not summary.get('overall_score') and obj.fit_score is None:
            return 'Eval failed'
        return summary.get('recommendation') or obj.fit_tier or '—'

    @admin.display(description='Apply URL')
    def application_link(self, obj):
        if not obj.application_url:
            return '—'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Open job</a>',
            obj.application_url,
        )

    @admin.display(description='Resume')
    def resume_link(self, obj):
        resume = obj.resume_for_apply
        if not resume:
            return '—'
        url = reverse('resume_builder:view_resume_by_id', args=[resume.pk])
        label = 'Open resume'
        if obj.optimized_resume_id:
            label = 'Open optimized'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            url,
            label,
        )

    @admin.action(description='Mark selected as applied')
    def mark_as_applied(self, request, queryset):
        done = 0
        for task in queryset.select_related(
            'user', 'job', 'user__ultimate_automation_profile', 'optimized_resume', 'source_resume'
        ):
            if task.status == MatchedTask.STATUS_APPLIED:
                continue
            complete_matched_task(task)
            done += 1
        self.message_user(
            request,
            f'Marked {done} task(s) as applied (JobApplication created when missing).',
            messages.SUCCESS,
        )

    def _mark_skipped(self, request, queryset, reason: str):
        done = 0
        for task in queryset:
            if task.status == MatchedTask.STATUS_SKIPPED and task.skip_reason == reason:
                continue
            skip_matched_task(task, reason=reason)
            done += 1
        self.message_user(
            request,
            f'Marked {done} task(s) as skipped ({reason}).',
            messages.SUCCESS,
        )

    @admin.action(description='Mark skipped — CAPTCHA')
    def mark_skipped_captcha(self, request, queryset):
        self._mark_skipped(request, queryset, 'captcha')

    @admin.action(description='Mark skipped — login required')
    def mark_skipped_login_required(self, request, queryset):
        self._mark_skipped(request, queryset, 'login_required')

    @admin.action(description='Mark skipped — job closed')
    def mark_skipped_job_closed(self, request, queryset):
        self._mark_skipped(request, queryset, 'job_closed')

    @admin.action(description='Mark skipped — geo blocked')
    def mark_skipped_geo_block(self, request, queryset):
        self._mark_skipped(request, queryset, 'geo_block')

    @admin.action(description='Mark skipped — other')
    def mark_skipped_other(self, request, queryset):
        self._mark_skipped(request, queryset, 'other')


@admin.register(StaffMatchRunPreferences)
class StaffMatchRunPreferencesAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'optimize_resume',
        'generate_cover_letter',
        'generate_why_should_hire',
        'updated_at',
    ]
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
