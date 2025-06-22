from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from resume_builder.models import Resume
from coverletter.models import CoverLetter
from .models import JobApplication

@login_required
def dashboard(request):
    """Main dashboard view"""
    # Get user's resumes for the selection
    resumes = request.user.resumes.all().order_by('-updated_at')
    cover_letters = CoverLetter.objects.filter(user=request.user)
    job_applications = request.user.dashboard_job_applications.all()
    
    context = {
        'resumes': resumes,
        'cover_letters': cover_letters,
        'job_applications': job_applications,
        'hero_content': {
            'page_title': 'Dashboard',
        }
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def job_applications_list(request):
    """View for listing all job applications"""
    job_applications = request.user.dashboard_job_applications.all()
    
    context = {
        'job_applications': job_applications,
        'hero_content': {
            'page_title': 'Recent Job Applications',
        }
    }
    
    return render(request, 'dashboard/job_applications_list.html', context)
