from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import time
import re
from resume_builder.models import Resume
from coverletter.models import CoverLetter
from ai_service.open_ai import generate_cover_letter_from_raw_text, optimize_my_resume_for_job
from .models import JobApplication

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
                    content_parts.append(f"• {achievement}")
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
                content_parts.append(f"{category}: {', '.join(skill_list)}")
            else:
                content_parts.append(f"{category}: {skill_list}")
        content_parts.append("")
    
    # Additional Information
    if resume.additional:
        content_parts.append("ADDITIONAL INFORMATION")
        for key, value in resume.additional.items():
            if isinstance(value, list):
                content_parts.append(f"{key}: {', '.join(value)}")
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

def _optimize_resume_for_job_application(user, job_description, resume, job_name):
    """
    Helper to optimize a resume for a job application using AI and create a new Resume object.
    Returns (optimized_resume, error_message)
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
        result = optimize_my_resume_for_job(job_description, resume_data)
        print(result)
        if not result:
            return None, 'AI did not return a result.'
        # Build new personal_info with optimized summary
        new_personal_info = dict(resume.personal_info) if resume.personal_info else {}
        if result.get('optimized_summary'):
            new_personal_info['summary'] = result['optimized_summary']
        # Map the new explicit skills structure back to the expected format (your model's keys)
        combined_skills = dict(resume.skills) if resume.skills else {}
        if result.get('reordered_technical_skills') is not None:
            combined_skills['technical'] = result['reordered_technical_skills']
        if result.get('reordered_soft_skills') is not None:
            combined_skills['soft'] = result['reordered_soft_skills']
        if result.get('reordered_languages') is not None:
            combined_skills['languages'] = result['reordered_languages']
        # Use reordered projects if present
        new_projects = result.get('reordered_projects', getattr(resume, 'projects', []))
        # Create the optimized Resume object
        optimized_resume = Resume.objects.create(
            user=user,
            name=f"Optimized for {job_name}",
            original_content=resume.original_content,
            personal_info=new_personal_info,
            experience=resume.experience,  # Optionally, you could use result['relevant_experience'] here if you want to replace experience
            education=resume.education,
            skills=combined_skills,
            additional=resume.additional,
            is_optimized=True,
            relevant_experience=result.get('relevant_experience', []),
            ats_score=result.get('ats_score', 0),
            keyword_matches=result.get('keyword_matches', []),
            improvement_suggestions=result.get('improvement_suggestions', []),
            optimized_content=result.get('optimized_summary', ''),
            template_id=resume.template_id,
        )
        # If your Resume model has a projects field, set it after creation
        if hasattr(optimized_resume, 'projects'):
            optimized_resume.projects = new_projects
            optimized_resume.save()
        return optimized_resume, None
    except Exception as e:
        return None, str(e)

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
                
                # Generate cover letter using AI
                result = generate_cover_letter_from_raw_text(
                    job_description, 
                    resume_content, 
                    applicant_name
                )
                
                processing_time = time.time() - start_time
                
                if result['success']:
                    cover_letter.content = result['cover_letter']
                    cover_letter.status = 'completed'
                    cover_letter.processing_time = processing_time
                    cover_letter.save()
                else:
                    cover_letter.status = 'failed'
                    cover_letter.error_message = result.get('error', 'Unknown error occurred')
                    cover_letter.processing_time = processing_time
                    cover_letter.save()
                    
            except Exception as e:
                cover_letter.status = 'failed'
                cover_letter.error_message = str(e)
                cover_letter.processing_time = time.time() - start_time
                cover_letter.save()
        
        optimized_resume = None
        error_message = None
        if optimize_resume:
            optimized_resume, error_message = _optimize_resume_for_job_application(
                request.user, job_description, resume, job_name
            )
        
        # Create job application record
        job_application = JobApplication.objects.create(
            user=request.user,
            job_name=job_name,
            cover_letter=cover_letter,
            resume=optimized_resume if optimized_resume else resume,
            status='completed' if not error_message else 'failed'
        )
        
        # Get updated counts
        resume_count = request.user.resumes.count()
        cover_letter_count = request.user.cover_letters.count()
        job_application_count = request.user.dashboard_job_applications.count()

        return JsonResponse({
            'status': 'completed' if not error_message else 'failed',
            'job_id': job_application.id,
            'job_name': job_application.job_name,
            'created_at': job_application.created_at.strftime('%M %d, %Y - %g:%i %A'),
            'resume_id': job_application.resume.id if job_application.resume else None,
            'cover_letter_id': cover_letter.id if cover_letter else None,
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
        job_application_count = request.user.dashboard_job_applications.count()

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
