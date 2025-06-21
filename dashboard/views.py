from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from resume_builder.models import Resume

@login_required
def dashboard(request):
    """Main dashboard view"""
    # Get user's resumes for the selection
    resumes = request.user.resumes.all().order_by('-updated_at')
    
    context = {
        'resumes': resumes,
        'hero_content': {
            'page_title': 'Dashboard',
            'page_description': 'Manage your resumes, cover letters, and job applications all in one place.'
        }
    }
    
    return render(request, 'dashboard/dashboard.html', context)
