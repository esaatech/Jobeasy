from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    JobSource, Job, JobApplication, UserJobPreferences,
    JobScrapingLog, ServicePackage, UserSubscription, JobApplicationRequest
)
from .services.ingestion import scrape_source


@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    change_form_template = 'admin/job_service/jobsource/change_form.html'
    list_display = [
        'name',
        'source_type',
        'board_kind',
        'is_active',
        'last_scraped',
        'job_count',
        'created_at',
    ]
    list_filter = ['source_type', 'is_active', 'created_at']
    search_fields = ['name', 'url']
    ordering = ['-created_at']
    readonly_fields = ['last_scraped', 'created_at', 'url_help']
    actions = ['scrape_selected_sources']
    fieldsets = (
        (None, {
            'fields': ('name', 'url', 'url_help', 'source_type', 'is_active'),
        }),
        ('Scraping', {
            'fields': ('last_scraped',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Board')
    def board_kind(self, obj):
        url = (obj.url or '').lower()
        if 'greenhouse.io' in url:
            return 'Greenhouse'
        if 'lever.co' in url:
            return 'Lever'
        if 'ashbyhq.com' in url:
            return 'Ashby'
        return '—'

    @admin.display(description='Jobs')
    def job_count(self, obj):
        count = obj.jobs.count()
        if not count:
            return '0'
        url = (
            reverse('admin:job_service_job_changelist')
            + f'?source__id__exact={obj.pk}'
        )
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description='URL format')
    def url_help(self, obj):
        return (
            'Greenhouse: https://boards.greenhouse.io/{company} — '
            'Lever: https://jobs.lever.co/{company} — '
            'Ashby: https://jobs.ashbyhq.com/{company}'
        )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<path:object_id>/scrape/',
                self.admin_site.admin_view(self.scrape_source_view),
                name='job_service_jobsource_scrape',
            ),
        ]
        return custom + urls

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            extra_context['scrape_url'] = reverse(
                'admin:job_service_jobsource_scrape',
                args=[object_id],
            )
            extra_context['jobs_changelist_url'] = (
                reverse('admin:job_service_job_changelist')
                + f'?source__id__exact={object_id}'
            )
            extra_context['logs_changelist_url'] = (
                reverse('admin:job_service_jobscrapinglog_changelist')
                + f'?source__id__exact={object_id}'
            )
        return super().changeform_view(request, object_id, form_url, extra_context)

    def scrape_source_view(self, request, object_id):
        source = get_object_or_404(JobSource, pk=object_id)
        if request.method != 'POST':
            return redirect('admin:job_service_jobsource_change', source.pk)

        if not self.has_change_permission(request, source):
            messages.error(request, 'You do not have permission to scrape this source.')
            return redirect('admin:job_service_jobsource_change', source.pk)

        fetch_details = request.POST.get('fetch_details') == '1'
        try:
            added, updated, deactivated, found = scrape_source(
                source, fetch_details=fetch_details
            )
        except Exception as exc:
            messages.error(
                request,
                f'Scrape failed for {source.name}: {exc}. '
                'See Job scraping logs for details.',
            )
            return redirect('admin:job_service_jobsource_change', source.pk)

        jobs_url = (
            reverse('admin:job_service_job_changelist')
            + f'?source__id__exact={source.pk}'
        )
        messages.success(
            request,
            format_html(
                'Scrape complete for <strong>{}</strong>: '
                'found={}, added={}, updated={}, deactivated={}. '
                '<a href="{}">View jobs</a>',
                source.name,
                found,
                added,
                updated,
                deactivated,
                jobs_url,
            ),
        )
        return redirect('admin:job_service_jobsource_change', source.pk)

    @admin.action(description='Scrape selected job sources')
    def scrape_selected_sources(self, request, queryset):
        ok = 0
        failed = 0
        for source in queryset:
            try:
                scrape_source(source, fetch_details=True)
                ok += 1
            except Exception as exc:
                failed += 1
                messages.error(request, f'{source.name}: {exc}')
        if ok:
            messages.success(request, f'Scraped {ok} source(s) successfully.')
        if failed:
            messages.warning(request, f'{failed} source(s) failed. Check scraping logs.')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'job_type', 'work_arrangement', 'application_url', 'posted_date', 'is_active', 'is_featured', 'is_curated', 'source', 'created_at']
    list_filter = ['job_type', 'work_arrangement', 'is_active', 'is_featured', 'is_curated', 'source', 'created_at', 'posted_date']
    search_fields = ['title', 'company', 'location', 'description', 'application_url']
    readonly_fields = ['job_id', 'created_at', 'updated_at']
    filter_horizontal = []
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('job_id', 'title', 'company', 'location', 'job_type', 'work_arrangement', 'application_url', 'posted_date')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'salary_currency'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('description', 'requirements', 'benefits')
        }),
        ('Metadata', {
            'fields': ('source', 'external_id', 'tags'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'is_curated')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'status', 'applied_at', 'updated_at']
    list_filter = ['status', 'applied_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'job__title', 'job__company']
    readonly_fields = ['applied_at', 'updated_at']
    ordering = ['-applied_at']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('user', 'job', 'status')
        }),
        ('Documents Used', {
            'fields': ('resume_used', 'cover_letter_used'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserJobPreferences)
class UserJobPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'remote_preference', 'notification_frequency', 'created_at']
    list_filter = ['remote_preference', 'notification_frequency', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Location Preferences', {
            'fields': ('preferred_locations', 'remote_preference')
        }),
        ('Job Preferences', {
            'fields': ('preferred_job_types', 'preferred_industries')
        }),
        ('Salary Preferences', {
            'fields': ('preferred_salary_min', 'preferred_salary_max'),
            'classes': ('collapse',)
        }),
        ('Skills', {
            'fields': ('required_skills', 'preferred_skills')
        }),
        ('Notifications', {
            'fields': ('notification_frequency',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(JobScrapingLog)
class JobScrapingLogAdmin(admin.ModelAdmin):
    list_display = ['source', 'status', 'jobs_found', 'jobs_added', 'jobs_updated', 'started_at', 'completed_at']
    list_filter = ['status', 'source', 'started_at']
    search_fields = ['source__name', 'error_message']
    readonly_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']
    
    fieldsets = (
        ('Scraping Details', {
            'fields': ('source', 'status', 'started_at', 'completed_at')
        }),
        ('Results', {
            'fields': ('jobs_found', 'jobs_added', 'jobs_updated')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'max_applications', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['price']
    
    fieldsets = (
        ('Package Information', {
            'fields': ('name', 'price', 'description')
        }),
        ('Features', {
            'fields': ('features', 'max_applications')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'status', 'applications_used', 'started_at', 'expires_at']
    list_filter = ['status', 'package', 'started_at']
    search_fields = ['user__username', 'user__email', 'package__name']
    readonly_fields = ['started_at']
    ordering = ['-started_at']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'package', 'status')
        }),
        ('Usage', {
            'fields': ('applications_used',)
        }),
        ('Timeline', {
            'fields': ('started_at', 'expires_at')
        }),
    )

@admin.register(JobApplicationRequest)
class JobApplicationRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_title', 'status', 'country', 'state_province', 'created_at', 'applications_submitted']
    list_filter = ['status', 'application_reason', 'city_preference', 'salary_expectations', 'created_at']
    search_fields = ['user__username', 'user__email', 'job_title', 'country', 'state_province']
    readonly_fields = ['request_id', 'created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('request_id', 'user', 'job_title', 'application_reason', 'other_reason')
        }),
        ('Resume Information', {
            'fields': ('resume_used', 'uploaded_resume'),
            'classes': ('collapse',)
        }),
        ('Location Preferences', {
            'fields': ('country', 'state_province', 'city_preference', 'specific_city', 'distance_preference')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'preferred_contact_method'),
            'classes': ('collapse',)
        }),
        ('Additional Preferences', {
            'fields': ('salary_expectations', 'salary_min', 'salary_max', 'start_date', 'additional_notes'),
            'classes': ('collapse',)
        }),
        ('Status & Results', {
            'fields': ('status', 'jobs_found', 'applications_submitted', 'interviews_scheduled', 'processing_notes')
        }),
        ('Processing Details', {
            'fields': ('ai_optimization_applied', 'cover_letters_generated'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'resume_used')
