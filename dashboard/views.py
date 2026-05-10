from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import time
import re
import logging
from django.urls import reverse
from resume_builder.models import Resume
from coverletter.models import CoverLetter
from job_service.models import JobApplicationRequest
from ai_service.cover_letter import generate_cover_letter_from_raw_text
from ai_service.resume_optimization import optimize_resume_for_job
from ai_service.prompt_formatting import (
    coerce_skill_list,
    format_bullet_item,
    format_items_for_prompt,
)
from .models import JobApplication
from subscriptions.models import UserSubscription, SubscriptionPlan

logger = logging.getLogger(__name__)

UNIFIED_STATUS_CHOICES = [
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('pending', 'Pending'),
    ('cancelled', 'Cancelled'),
]


def get_unified_job_applications(user):
    """
    Merge dashboard-generated job applications and job_service requests.
    Returns a normalized list sorted newest-first.
    """
    dashboard_items = user.dashboard_job_applications.select_related('resume', 'cover_letter').all()
    service_requests = user.job_application_requests.select_related('resume_used').all()

    unified = []

    for app in dashboard_items:
        unified.append({
            'id': app.id,
            'source': 'dashboard',
            'source_id': app.id,
            'job_name': app.job_name,
            'job_title': app.job_name,
            'status': app.status,
            'status_display': app.get_status_display(),
            'created_at': app.created_at,
            'resume': app.resume,
            'cover_letter': app.cover_letter,
            'can_email': app.status == 'completed' or app.cover_letter is not None,
            'can_delete': True,
            'detail_url': None,
        })

    for req in service_requests:
        unified.append({
            'id': req.id,
            'source': 'job_service_request',
            'source_id': req.id,
            'job_name': req.job_title,
            'job_title': req.job_title,
            'status': req.status,
            'status_display': req.get_status_display(),
            'created_at': req.created_at,
            'resume': req.resume_used,
            'cover_letter': None,
            'can_email': False,
            'can_delete': False,
            'detail_url': reverse('job_service:application_status', args=[req.request_id]),
            'jobs_found': req.jobs_found,
            'applications_submitted': req.applications_submitted,
            'interviews_scheduled': req.interviews_scheduled,
            'cover_letters_generated': req.cover_letters_generated,
            'location_display': req.get_location_display(),
            'can_cancel': req.can_cancel,
            'request_id': req.request_id,
        })

    unified.sort(key=lambda item: item['created_at'], reverse=True)
    return unified

def _format_resume_content(resume):
    """Format resume's structured data into readable text for generating cover letter"""
    content_parts = []
    
    # Personal Information
    if resume.personal_info:
        personal = resume.personal_info
        content_parts.append(f"PERSONAL INFORMATION")
        content_parts.append(f"Name: {personal.get('full_name', 'N/A')}")
        content_parts.append(f"Email: {personal.get('email', 'N/A')}")
        content_parts.append(f"Phone: {personal.get('phone', 'N/A')}")
        if personal.get('location'):
            content_parts.append(f"Location: {personal['location']}")
        if personal.get('linkedin'):
            content_parts.append(f"LinkedIn: {personal['linkedin']}")
        content_parts.append("")
    
    # Professional Summary
    if resume.personal_info and resume.personal_info.get('summary'):
        content_parts.append("PROFESSIONAL SUMMARY")
        content_parts.append(resume.personal_info['summary'])
        content_parts.append("")
    
    # Experience
    if resume.experience:
        content_parts.append("PROFESSIONAL EXPERIENCE")
        for exp in resume.experience:
            content_parts.append(f"{exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
            if exp.get('duration'):
                content_parts.append(f"Duration: {exp['duration']}")
            if exp.get('description'):
                content_parts.append(f"Description: {exp['description']}")
            if exp.get('achievements'):
                content_parts.append("Key Achievements:")
                for achievement in exp['achievements']:
                    content_parts.append(f"• {format_bullet_item(achievement)}")
            content_parts.append("")
    
    # Education
    if resume.education:
        content_parts.append("EDUCATION")
        for edu in resume.education:
            content_parts.append(f"{edu.get('degree', 'N/A')} - {edu.get('institution', 'N/A')}")
            if edu.get('year'):
                content_parts.append(f"Year: {edu['year']}")
            if edu.get('gpa'):
                content_parts.append(f"GPA: {edu['gpa']}")
            content_parts.append("")
    
    # Skills
    if resume.skills:
        content_parts.append("SKILLS")
        for category, skill_list in resume.skills.items():
            if isinstance(skill_list, list):
                content_parts.append(f"{category}: {format_items_for_prompt(skill_list)}")
            else:
                content_parts.append(f"{category}: {skill_list}")
        content_parts.append("")
    
    # Additional Information
    if resume.additional:
        content_parts.append("ADDITIONAL INFORMATION")
        for key, value in resume.additional.items():
            if isinstance(value, list):
                content_parts.append(f"{key}: {format_items_for_prompt(value)}")
            else:
                content_parts.append(f"{key}: {value}")
        content_parts.append("")
    
    # If no structured content, fall back to original content
    if not content_parts:
        return resume.original_content or "No resume content available."
    
    return "\n".join(content_parts)

@login_required
def dashboard(request):
    """Main dashboard view"""
    # Get user's resumes for the selection (excluding optimized resumes)
    resumes = request.user.resumes.filter(is_optimized=False).order_by('-updated_at')
    cover_letters = CoverLetter.objects.filter(user=request.user)
    job_applications = get_unified_job_applications(request.user)

    # Get user's current subscription (active)
    current_subscription = UserSubscription.objects.filter(
        user=request.user,
        status='ACTIVE'
    ).select_related('plan', 'plan_duration').first()
    if not current_subscription:
        free_plan = SubscriptionPlan.objects.filter(name='Free', is_active=True).first()
        if free_plan:
            current_subscription = type('obj', (object,), {
                'plan': free_plan,
                'plan_duration': None,
                'status': 'ACTIVE'
            })()

    context = {
        'resumes': resumes,
        'cover_letters': cover_letters,
        'job_applications': job_applications,
        'job_application_count': len(job_applications),
        'current_subscription': current_subscription,
        'hero_content': {
            'page_title': 'Dashboard',
        }
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def job_applications_list(request):
    """View for listing all job applications"""
    job_applications = get_unified_job_applications(request.user)
    
    context = {
        'job_applications': job_applications,
        'job_application_count': len(job_applications),
        'hero_content': {
            'page_title': 'Recent Job Applications',
        }
    }
    
    return render(request, 'dashboard/job_applications_list.html', context)

def _optimize_resume_for_job_application(user, job_description, resume, job_name, include_email_subject=True):
    """
    Helper to optimize a resume for a job application using AI and create a new Resume object.
    Returns (optimized_resume, error_message, optimization_result)
    
    Args:
        user: The user requesting the optimization
        job_description: The job posting description
        resume: The original resume object to optimize
        job_name: The job name for the optimized resume title
        include_email_subject: Whether to generate an email subject (default: True)
    """
    # Prepare structured resume data for the AI function
    # Extract skills from the existing skills structure using correct keys
    existing_skills = resume.skills or {}
    technical_skills = existing_skills.get('technical', [])
    soft_skills = existing_skills.get('soft', [])
    languages = existing_skills.get('languages', [])
    
    resume_data = {
        'professional_summary': resume.personal_info.get('summary', ''),
        'experience': resume.experience,
        'technical_skills': technical_skills,
        'soft_skills': soft_skills,
        'languages': languages,
        'projects': getattr(resume, 'projects', []),  # If you have a projects field
    }
    try:
        logger.info(
            "dashboard.optimize: start resume_id=%s user=%s job_name=%r",
            getattr(resume, "id", None),
            getattr(user, "id", None),
            job_name,
        )
        result = optimize_resume_for_job(job_description, resume_data, include_email_subject=include_email_subject)
        if result.get("success") is False:
            err = result.get("error", "Resume optimization failed")
            logger.warning("dashboard.optimize: AI service error: %s", err)
            return None, err, result
        if not result:
            return None, 'AI did not return a result.', None
        # Build new personal_info with optimized summary
        new_personal_info = dict(resume.personal_info) if resume.personal_info else {}
        summary = result.get("optimized_summary")
        if isinstance(summary, str) and summary.strip():
            new_personal_info["summary"] = summary.strip()
        # Map the new explicit skills structure back to the expected format (your model's keys)
        combined_skills = dict(resume.skills) if resume.skills else {}
        if result.get("reordered_technical_skills") is not None:
            combined_skills["technical"] = coerce_skill_list(result["reordered_technical_skills"])
        if result.get("reordered_soft_skills") is not None:
            combined_skills["soft"] = coerce_skill_list(result["reordered_soft_skills"])
        if result.get("reordered_languages") is not None:
            combined_skills["languages"] = coerce_skill_list(result["reordered_languages"])
        # Use reordered projects if present
        new_projects = result.get("reordered_projects", getattr(resume, "projects", []))

        # Get AI-generated title for the resume
        resume_title = result.get("title", f"Optimized for {job_name}")

        opt_text = result.get("optimized_summary") or ""
        if not isinstance(opt_text, str):
            opt_text = str(opt_text)

        # Create the optimized Resume object
        optimized_resume = Resume.objects.create(
            user=user,
            name=resume_title,  # Use AI-generated title
            original_content=resume.original_content,
            personal_info=new_personal_info,
            experience=resume.experience,  # Source timeline unchanged; relevant_experience holds AI-ranked copy
            education=resume.education,
            skills=combined_skills,
            additional=resume.additional,
            is_optimized=True,
            relevant_experience=result.get("relevant_experience", []),
            ats_score=result.get("ats_score", 0),
            keyword_matches=result.get("keyword_matches", []),
            improvement_suggestions=result.get("improvement_suggestions", []),
            optimized_content=opt_text,
            template_id=resume.template_id,
        )
        # If your Resume model has a projects field, set it after creation
        if hasattr(optimized_resume, "projects"):
            optimized_resume.projects = new_projects
            optimized_resume.save()
        logger.info(
            "dashboard.optimize: created optimized_resume_id=%s summary_len=%s",
            optimized_resume.id,
            len(new_personal_info.get("summary") or ""),
        )
        return optimized_resume, None, result
    except Exception as e:
        logger.exception("dashboard.optimize: exception")
        return None, str(e), None

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
        
        # Get the resume
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        
        # Extract job name from description (simple approach)
        job_name = job_description[:50] + "..." if len(job_description) > 50 else job_description
        
        cover_letter = None
        # Set before cover-letter branch so JobApplication creation never reads an unbound local
        # when cover_letter exists but the try block fails before assignment.
        cover_letter_result = None

        # Generate cover letter if requested
        if generate_cover_letter:
            start_time = time.time()
            
            # Create cover letter record
            cover_letter = CoverLetter.objects.create(
                user=request.user,
                title=f"Cover Letter for {job_name}",
                job_description=job_description,
                status='processing'
            )
            
            try:
                # Get applicant name from resume
                applicant_name = resume.personal_info.get('full_name', 'Applicant')
                if not applicant_name:
                    applicant_name = resume.name
                
                # Get resume content from structured fields
                resume_content = _format_resume_content(resume)
                
                # Generate cover letter using AI (with email subject generation)
                cover_letter_result = generate_cover_letter_from_raw_text(
                    job_description, 
                    resume_content, 
                    applicant_name,
                    include_email_subject=True  # Generate email subject as well
                )
                
                processing_time = time.time() - start_time
                
                if cover_letter_result['success']:
                    cover_letter.content = cover_letter_result['cover_letter']
                    # Update title if provided by AI
                    if cover_letter_result.get('title'):
                        cover_letter.title = cover_letter_result['title']
                        # Update job_name to use the AI-generated title
                        job_name = cover_letter_result['title']
                    cover_letter.status = 'completed'
                    cover_letter.processing_time = processing_time
                    cover_letter.save()
                else:
                    cover_letter.status = 'failed'
                    cover_letter.error_message = cover_letter_result.get('error', 'Unknown error occurred')
                    cover_letter.processing_time = processing_time
                    cover_letter.save()
                    
            except Exception as e:
                cover_letter.status = 'failed'
                cover_letter.error_message = str(e)
                cover_letter.processing_time = time.time() - start_time
                cover_letter.save()
        
        optimized_resume = None
        error_message = None
        resume_email_subject = None
        resume_title = None
        if optimize_resume:
            # Only generate email subject for resume if no cover letter is being generated
            # This ensures cover letter takes priority for email subject when both are selected
            include_resume_email_subject = not generate_cover_letter
            
            optimized_resume, error_message, optimization_result = _optimize_resume_for_job_application(
                request.user, job_description, resume, job_name, include_resume_email_subject
            )
            # Get email subject and title from resume optimization if available
            if optimized_resume and optimization_result:
                resume_email_subject = optimization_result.get('email_subject')
                resume_title = optimization_result.get('title')
                # Update job_name to use the AI-generated title from resume optimization
                if resume_title:
                    job_name = resume_title
        
        # Create job application record
        job_application = JobApplication.objects.create(
            user=request.user,
            job_name=job_name,
            cover_letter=cover_letter,
            resume=optimized_resume if optimize_resume and optimized_resume else None,
            email_subject=(
                cover_letter_result.get('email_subject')
                if (
                    cover_letter
                    and cover_letter_result
                    and cover_letter_result.get('success')
                )
                else resume_email_subject
            ),
            status='completed' if not error_message else 'failed'
        )
        
        # Get updated counts
        resume_count = request.user.resumes.count()
        cover_letter_count = request.user.cover_letters.count()
        job_application_count = len(get_unified_job_applications(request.user))

        return JsonResponse({
            'status': 'completed' if not error_message else 'failed',
            'job_id': job_application.id,
            'job_name': job_application.job_name,
            'created_at': job_application.created_at.strftime('%M %d, %Y - %g:%i %A'),
            'resume_id': job_application.resume.id if job_application.resume else None,
            'cover_letter_id': cover_letter.id if cover_letter else None,
            'email_subject': job_application.email_subject,
            'error': error_message,
            'counts': {
                'resumes': resume_count,
                'cover_letters': cover_letter_count,
                'job_applications': job_application_count
            }
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
        
        # If a cover letter is associated, delete it first
        if job_application.cover_letter:
            job_application.cover_letter.delete()
        # If a resume is associated, delete it as well
        if job_application.resume:
            job_application.resume.delete()
        # Delete the job application
        job_application.delete()
        
        # Get updated counts
        resume_count = request.user.resumes.count()
        cover_letter_count = request.user.cover_letters.count()
        job_application_count = len(get_unified_job_applications(request.user))

        return JsonResponse({
            'status': 'success',
            'message': 'Job application and associated cover letter and resume deleted successfully',
            'counts': {
                'resumes': resume_count,
                'cover_letters': cover_letter_count,
                'job_applications': job_application_count
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)
