from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
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

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def generate_job_application(request):
    """API endpoint to generate job application"""
    try:
        # Parse form data
        resume_id = request.POST.get('resume_id')
        job_description = request.POST.get('job_description')
        optimize_resume = request.POST.get('optimize_resume') == 'true'
        generate_cover_letter = request.POST.get('generate_cover_letter') == 'true'
        
        # Validate inputs
        if not resume_id or not job_description:
            return JsonResponse({
                'status': 'failed',
                'error': 'Missing required fields'
            }, status=400)
        
        # Extract job name from description (simple approach)
        job_name = job_description[:50] + "..." if len(job_description) > 50 else job_description
        
        # Create job application record
        job_application = JobApplication.objects.create(
            user=request.user,
            job_name=job_name,
            status='processing'
        )
        
        # TODO: Add actual processing logic here
        # For now, simulate processing and return completed state
        import time
        time.sleep(2)  # Simulate processing time
        
        # Update job application with completed status
        job_application.status = 'completed'
        job_application.resume_link = '/media/resumes/sample_resume.pdf'  # Placeholder
        job_application.cover_letter_link = '/media/cover_letters/sample_cover_letter.pdf'  # Placeholder
        job_application.save()
        
        return JsonResponse({
            'status': 'completed',
            'job_id': job_application.id,
            'job_name': job_application.job_name,
            'created_at': job_application.created_at.strftime('%M %d, %Y - %g:%i %A'),
            'resume_link': job_application.resume_link,
            'cover_letter_link': job_application.cover_letter_link
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'failed',
            'error': str(e)
        }, status=500)

@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_job_application(request, job_id):
    """API endpoint to delete job application"""
    try:
        # Get the job application and ensure it belongs to the user
        job_application = get_object_or_404(JobApplication, id=job_id, user=request.user)
        
        # Delete the job application
        job_application.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Job application deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)
