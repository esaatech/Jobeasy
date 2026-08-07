from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import ApplyTask, UltimateAutomationProfile
from .services.apply_tasks import complete_apply_task, skip_apply_task
from .services.job_matcher import (
    profile_is_match_ready,
    run_match_cycle,
    ultimate_subscriber_user_ids,
)


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

        if request.method == 'POST' and request.POST.get('run_match'):
            raw_ids = request.POST.getlist('user_ids')
            user_ids = []
            for value in raw_ids:
                try:
                    user_ids.append(int(value))
                except (TypeError, ValueError):
                    continue

            # Only Ultimate/Test subscribers may be matched from this page.
            allowed = set(ultimate_subscriber_user_ids())
            user_ids = [uid for uid in user_ids if uid in allowed]

            if not user_ids:
                messages.warning(request, 'No Ultimate/Test users selected.')
                return redirect('admin:automation_ultimateautomationprofile_match')

            # Ensure a profile row exists so the matcher can evaluate them.
            User = get_user_model()
            for user in User.objects.filter(pk__in=user_ids):
                UltimateAutomationProfile.objects.get_or_create(user=user)

            result = run_match_cycle(user_ids=user_ids)
            tasks_url = reverse('admin:automation_applytask_changelist')
            messages.success(
                request,
                format_html(
                    'Match complete for {} user(s): '
                    'created {} new ApplyTask(s) '
                    '(existing user+job pairs skipped). '
                    '<a href="{}">View Apply tasks</a>',
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
            return redirect('admin:automation_applytask_changelist')

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
        }
        return render(request, 'admin/automation/match_ultimate_users.html', context)


@admin.register(ApplyTask)
class ApplyTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'job_title',
        'company',
        'job_location',
        'work_arrangement',
        'status',
        'application_link',
        'created_at',
        'applied_at',
    ]
    list_filter = ['status', 'skip_reason', 'job__work_arrangement', 'created_at']
    search_fields = [
        'user__username',
        'user__email',
        'job__title',
        'job__company',
        'application_url',
    ]
    readonly_fields = ['created_at', 'updated_at', 'applied_at']
    raw_id_fields = ['user', 'job']
    ordering = ['created_at']
    list_select_related = ['user', 'job']
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
        ('Operator', {
            'fields': ('skip_reason', 'operator_notes', 'applied_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'job')

    def changelist_view(self, request, extra_context=None):
        # Default to the operator queue (queued) when no status filter is set.
        if (
            request.method == 'GET'
            and 'status__exact' not in request.GET
            and 'status' not in request.GET
        ):
            params = request.GET.copy()
            params['status__exact'] = ApplyTask.STATUS_QUEUED
            return HttpResponseRedirect(f'{request.path}?{params.urlencode()}')
        return super().changelist_view(request, extra_context=extra_context)

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

    @admin.display(description='Apply URL')
    def application_link(self, obj):
        if not obj.application_url:
            return '—'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Open</a>',
            obj.application_url,
        )

    @admin.action(description='Mark selected as applied')
    def mark_as_applied(self, request, queryset):
        done = 0
        for task in queryset.select_related('user', 'job', 'user__ultimate_automation_profile'):
            if task.status == ApplyTask.STATUS_APPLIED:
                continue
            complete_apply_task(task)
            done += 1
        self.message_user(
            request,
            f'Marked {done} task(s) as applied (JobApplication created when missing).',
            messages.SUCCESS,
        )

    def _mark_skipped(self, request, queryset, reason: str):
        done = 0
        for task in queryset:
            if task.status == ApplyTask.STATUS_SKIPPED and task.skip_reason == reason:
                continue
            skip_apply_task(task, reason=reason)
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
