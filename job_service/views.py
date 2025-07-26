from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Job, JobApplication, UserJobPreferences, ServicePackage, UserSubscription, JobApplicationRequest
from .forms import JobApplicationForm
from resume_builder.models import Resume
import json

def job_application_service(request):
    """Main job application service landing page - now focused on the complete process"""
    
    if not request.user.is_authenticated:
        return redirect('auth:login')
    
    # Get user's existing application requests
    user_requests = JobApplicationRequest.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get user's resumes
    user_resumes = Resume.objects.filter(user=request.user).order_by('-created_at')
    
    # Check if user has Ultimate subscription
    from subscriptions.models import UserSubscription
    active_subscription = UserSubscription.objects.filter(
        user=request.user,
        status='ACTIVE'
    ).select_related('plan').first()
    
    is_ultimate = active_subscription and active_subscription.plan.name == 'Ultimate'
    
    # Hero section content
    hero_content = {
        'title': 'Complete Job Application Service',
        'description': 'We handle your entire job search process. From finding opportunities to submitting applications - we do it all for you.',
        'features': [
            'AI-Powered Job Matching',
            'Automated Application Submission',
            'Resume Optimization',
            'Cover Letter Generation',
            'Application Tracking'
        ]
    }
    
    # Service statistics
    service_stats = {
        'total_requests': JobApplicationRequest.objects.count(),
        'completed_requests': JobApplicationRequest.objects.filter(status='completed').count(),
        'total_applications': JobApplicationRequest.objects.aggregate(
            total=Sum('applications_submitted')
        )['total'] or 0,
        'success_rate': '85%'  # Placeholder
    }
    
    context = {
        'hero_content': hero_content,
        'user_requests': user_requests,
        'user_resumes': user_resumes,
        'service_stats': service_stats,
        'has_resumes': user_resumes.exists(),
        'is_ultimate': is_ultimate
    }
    
    return render(request, 'job_service/job_application_service.html', context)

@login_required
def start_job_application(request):
    """Start a new job application process"""
    
    # Check if user has resumes
    user_resumes = Resume.objects.filter(user=request.user).order_by('-created_at')
    has_resumes = user_resumes.exists()
    
    if request.method == 'POST':
        # Check if user has resumes first
        if not has_resumes:
            messages.error(request, 'You need to create a resume before we can start your job search.')
            return redirect('resume_builder:create_resume')
        
        form = JobApplicationForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            
            # Create the job application request
            application_request = JobApplicationRequest.objects.create(
                user=request.user,
                job_title=form.cleaned_data['job_title'],
                application_reason=form.cleaned_data['application_reason'],
                other_reason=form.cleaned_data.get('other_reason', ''),
                # New location fields
                countries=form.cleaned_data.get('countries', []),
                work_arrangements=form.cleaned_data.get('work_arrangements', []),
                city=form.cleaned_data.get('city', ''),
                distance=form.cleaned_data.get('distance'),
                # Old fields (keep for compatibility, but not used by frontend)
                country=form.cleaned_data.get('country', ''),
                state_province=form.cleaned_data.get('state_province', ''),
                city_preference=form.cleaned_data.get('city_preference', ''),
                specific_city=form.cleaned_data.get('specific_city', ''),
                distance_preference=form.cleaned_data.get('distance_preference', ''),
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                preferred_contact_method=form.cleaned_data['preferred_contact_method'],
                salary_expectations=form.cleaned_data['salary_expectations'],
                salary_min=form.cleaned_data.get('salary_min'),
                salary_max=form.cleaned_data.get('salary_max'),
                start_date=form.cleaned_data['start_date'],
                additional_notes=form.cleaned_data.get('additional_notes', '')
            )
            
            # Automatically select the most recent resume
            if has_resumes:
                application_request.resume_used = user_resumes.first()
            
            application_request.save()
            
            messages.success(request, 'Your job application request has been submitted successfully! We\'ll start processing it right away.')
            return redirect('job_service:application_status', request_id=application_request.request_id)
    else:
        form = JobApplicationForm(user=request.user)
    
    context = {
        'form': form,
        'step': 1,
        'has_resumes': has_resumes,
        'user_resumes': user_resumes[:3] if has_resumes else None  # Show first 3 resumes for context
    }
    
    return render(request, 'job_service/start_application.html', context)

@login_required
def application_status(request, request_id):
    """View the status of a job application request"""
    
    application_request = get_object_or_404(JobApplicationRequest, request_id=request_id, user=request.user)
    
    context = {
        'application_request': application_request,
        'can_cancel': application_request.can_cancel
    }
    
    return render(request, 'job_service/application_status.html', context)

@login_required
def cancel_application(request, request_id):
    """Cancel a job application request"""
    
    if request.method == 'POST':
        application_request = get_object_or_404(JobApplicationRequest, request_id=request_id, user=request.user)
        
        if application_request.can_cancel:
            application_request.status = 'cancelled'
            application_request.save()
            messages.success(request, 'Your job application request has been cancelled.')
        else:
            messages.error(request, 'This request cannot be cancelled.')
    
    return redirect('dashboard:dashboard')

@login_required
def my_applications(request):
    """View all user's job application requests"""
    
    applications = JobApplicationRequest.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(applications, 10)
    page = request.GET.get('page', 1)
    applications_page = paginator.get_page(page)
    
    context = {
        'applications': applications_page,
        'status_filter': status_filter,
        'status_choices': JobApplicationRequest.status.field.choices,
    }
    
    return render(request, 'job_service/my_applications.html', context)

@login_required
def job_dashboard(request):
    """User dashboard for job applications and tracking"""
    
    # Get user's active subscription
    active_subscription = UserSubscription.objects.filter(
        user=request.user, 
        status='active'
    ).first()
    
    # Get user's job preferences
    preferences, created = UserJobPreferences.objects.get_or_create(user=request.user)
    
    # Get user's recent applications
    recent_applications = JobApplication.objects.filter(user=request.user)[:5]
    
    # Get recommended jobs based on preferences
    recommended_jobs = get_recommended_jobs(request.user, limit=6)
    
    # Get application statistics
    application_stats = {
        'total_applied': JobApplication.objects.filter(user=request.user).count(),
        'under_review': JobApplication.objects.filter(user=request.user, status='under_review').count(),
        'interview_scheduled': JobApplication.objects.filter(user=request.user, status='interview_scheduled').count(),
        'hired': JobApplication.objects.filter(user=request.user, status='hired').count(),
    }
    
    context = {
        'active_subscription': active_subscription,
        'preferences': preferences,
        'recent_applications': recent_applications,
        'recommended_jobs': recommended_jobs,
        'application_stats': application_stats,
    }
    
    return render(request, 'job_service/dashboard.html', context)

@login_required
def job_listings(request):
    """Browse and search job listings"""
    
    # Get filter parameters
    search = request.GET.get('search', '')
    location = request.GET.get('location', '')
    job_type = request.GET.get('job_type', '')
    remote = request.GET.get('remote', '')
    page = request.GET.get('page', 1)
    
    # Build query
    jobs = Job.objects.filter(is_active=True)
    
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(company__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__contains=[search])
        )
    
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    if remote:
        if remote == 'remote_only':
            jobs = jobs.filter(location__icontains='remote')
        elif remote == 'onsite':
            jobs = jobs.exclude(location__icontains='remote')
    
    # Pagination
    paginator = Paginator(jobs, 12)
    jobs_page = paginator.get_page(page)
    
    # Get user's applied jobs for comparison
    applied_job_ids = JobApplication.objects.filter(
        user=request.user
    ).values_list('job_id', flat=True)
    
    context = {
        'jobs': jobs_page,
        'applied_job_ids': list(applied_job_ids),
        'search': search,
        'location': location,
        'job_type': job_type,
        'remote': remote,
        'job_types': Job.job_type.field.choices,
    }
    
    return render(request, 'job_service/job_listings.html', context)

@login_required
def job_detail(request, job_id):
    """Detailed view of a job posting"""
    
    job = get_object_or_404(Job, job_id=job_id, is_active=True)
    
    # Check if user has already applied
    has_applied = JobApplication.objects.filter(user=request.user, job=job).exists()
    
    # Get similar jobs
    similar_jobs = Job.objects.filter(
        is_active=True,
        tags__overlap=job.tags
    ).exclude(job_id=job.job_id)[:3]
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'similar_jobs': similar_jobs,
    }
    
    return render(request, 'job_service/job_detail.html', context)

@login_required
def apply_to_job(request, job_id):
    """Apply to a job"""
    
    if request.method == 'POST':
        job = get_object_or_404(Job, job_id=job_id, is_active=True)
        
        # Check if already applied
        if JobApplication.objects.filter(user=request.user, job=job).exists():
            return JsonResponse({
                'success': False,
                'error': 'You have already applied to this job'
            })
        
        # Check subscription limits
        active_subscription = UserSubscription.objects.filter(
            user=request.user, 
            status='active'
        ).first()
        
        if active_subscription and active_subscription.package.max_applications:
            if active_subscription.applications_used >= active_subscription.package.max_applications:
                return JsonResponse({
                    'success': False,
                    'error': 'You have reached your application limit for this package'
                })
        
        # Create application
        application = JobApplication.objects.create(
            user=request.user,
            job=job,
            status='applied'
        )
        
        # Update subscription usage
        if active_subscription:
            active_subscription.applications_used += 1
            active_subscription.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Application submitted successfully'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def application_tracking(request):
    """Track all job applications"""
    
    applications = JobApplication.objects.filter(user=request.user).order_by('-applied_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(applications, 10)
    page = request.GET.get('page', 1)
    applications_page = paginator.get_page(page)
    
    context = {
        'applications': applications_page,
        'status_filter': status_filter,
        'status_choices': JobApplication.status.field.choices,
    }
    
    return render(request, 'job_service/application_tracking.html', context)

@login_required
def update_application_status(request, application_id):
    """Update application status"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            application = get_object_or_404(JobApplication, id=application_id, user=request.user)
            
            new_status = data.get('status')
            notes = data.get('notes', '')
            
            if new_status in dict(JobApplication.status.field.choices):
                application.status = new_status
                application.notes = notes
                application.save()
                
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid status'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def user_preferences(request):
    """Manage user job preferences"""
    
    preferences, created = UserJobPreferences.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            preferences.preferred_locations = data.get('preferred_locations', [])
            preferences.preferred_job_types = data.get('preferred_job_types', [])
            preferences.preferred_salary_min = data.get('preferred_salary_min')
            preferences.preferred_salary_max = data.get('preferred_salary_max')
            preferences.preferred_industries = data.get('preferred_industries', [])
            preferences.required_skills = data.get('required_skills', [])
            preferences.preferred_skills = data.get('preferred_skills', [])
            preferences.remote_preference = data.get('remote_preference', 'any')
            preferences.notification_frequency = data.get('notification_frequency', 'weekly')
            
            preferences.save()
            
            return JsonResponse({'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    
    context = {
        'preferences': preferences,
        'job_types': Job.job_type.field.choices,
        'remote_choices': UserJobPreferences.remote_preference.field.choices,
        'notification_choices': UserJobPreferences.notification_frequency.field.choices,
    }
    
    return render(request, 'job_service/preferences.html', context)

def get_recommended_jobs(user, limit=6):
    """Get job recommendations based on user preferences"""
    
    try:
        preferences = UserJobPreferences.objects.get(user=user)
        
        # Build recommendation query
        jobs = Job.objects.filter(is_active=True)
        
        # Filter by preferred locations
        if preferences.preferred_locations:
            location_query = Q()
            for location in preferences.preferred_locations:
                location_query |= Q(location__icontains=location)
            jobs = jobs.filter(location_query)
        
        # Filter by preferred job types
        if preferences.preferred_job_types:
            jobs = jobs.filter(job_type__in=preferences.preferred_job_types)
        
        # Filter by remote preference
        if preferences.remote_preference == 'remote_only':
            jobs = jobs.filter(location__icontains='remote')
        elif preferences.remote_preference == 'onsite':
            jobs = jobs.exclude(location__icontains='remote')
        
        # Filter by skills (if available)
        if preferences.required_skills or preferences.preferred_skills:
            skills_query = Q()
            all_skills = preferences.required_skills + preferences.preferred_skills
            for skill in all_skills:
                skills_query |= Q(tags__contains=[skill])
            jobs = jobs.filter(skills_query)
        
        # Exclude already applied jobs
        applied_job_ids = JobApplication.objects.filter(user=user).values_list('job_id', flat=True)
        jobs = jobs.exclude(job_id__in=applied_job_ids)
        
        return jobs[:limit]
        
    except UserJobPreferences.DoesNotExist:
        # Return featured jobs if no preferences set
        return Job.objects.filter(is_featured=True, is_active=True)[:limit]

def interview_prep(request):
    """Render the interview prep page."""
    from question_answer.models import Category
    
    # Get all categories for the dropdown
    categories = Category.objects.all().order_by('name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'job_service/interview_prep.html', context)
