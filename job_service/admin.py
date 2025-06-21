from django.contrib import admin
from .models import (
    JobSource, Job, JobApplication, UserJobPreferences, 
    JobScrapingLog, ServicePackage, UserSubscription
)

@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'is_active', 'last_scraped', 'created_at']
    list_filter = ['source_type', 'is_active', 'created_at']
    search_fields = ['name', 'url']
    ordering = ['-created_at']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'job_type', 'is_active', 'is_featured', 'is_curated', 'created_at']
    list_filter = ['job_type', 'is_active', 'is_featured', 'is_curated', 'source', 'created_at']
    search_fields = ['title', 'company', 'location', 'description']
    readonly_fields = ['job_id', 'created_at', 'updated_at']
    filter_horizontal = []
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('job_id', 'title', 'company', 'location', 'job_type')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'salary_currency'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('description', 'requirements', 'benefits')
        }),
        ('Metadata', {
            'fields': ('source', 'external_id', 'tags', 'posted_date'),
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
