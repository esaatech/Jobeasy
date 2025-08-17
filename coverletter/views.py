"""
Cover Letter Views

This module handles all cover letter-related views including:
- PDF generation and download
- Cover letter editing and saving
- Web interface for viewing cover letters

The PDF generation uses the PDF Generator app with Playwright to create
high-quality, professional cover letters that fit on a single page.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from ai_service.cover_letter import generate_cover_letter_from_raw_text
from .models import CoverLetter
import logging
import json

# Get the logger for this app
logger = logging.getLogger('home')

# Create your views here.
def index(request):
    return render(request, 'coverletter/index.html')   

@login_required
def cover_letter_view(request, cover_letter_id):
    """View to display a specific cover letter"""
    cover_letter = get_object_or_404(CoverLetter, id=cover_letter_id, user=request.user)
    
    context = {
        'cover_letter': cover_letter,  # Pass the full cover_letter object
        'page_title': 'Cover Letter Generated',
        'page_description': 'Your AI-generated cover letter is ready!'
    }
    
    return render(request, 'coverletter/cover_letter_response.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def job_cover_letter(request):
    print(f"........in job_cover_letter..........")
    if request.method == "GET":
        # Get user's resumes for the selection component (excluding optimized resumes)
        from resume_builder.models import Resume
        resumes = Resume.objects.filter(user=request.user, is_optimized=False).order_by('-updated_at')
        
        context = {
            'page_title': 'Cover Letter AI',
            'page_description': 'Generate a professional cover letter using AI',
            'meta_description': 'Create a customized cover letter instantly with our AI-powered tool.',
            'resumes': resumes,  # Add resumes for the selection component
        }
        return render(request, 'coverletter/job_cover_letter.html', context)
    
    try:
        data = request.POST
        selected_resume_id = data.get('selected_resume')
        uploaded_file = request.FILES.get('resume')
        job_text = data.get('job_posting')

        # Debug: Log received data
        print(f"=== DEBUG: Cover Letter Form Data ===")
        print(f"POST data: {dict(data)}")
        print(f"FILES: {list(request.FILES.keys()) if request.FILES else 'None'}")
        print(f"selected_resume_id: {selected_resume_id}")
        print(f"uploaded_file: {uploaded_file}")
        print(f"job_text length: {len(job_text) if job_text else 0}")
        print(f"=====================================")
        
        logger.info(f"Received form data: POST={dict(data)}, FILES={list(request.FILES.keys()) if request.FILES else 'None'}")
        logger.info(f"selected_resume_id: {selected_resume_id}")
        logger.info(f"uploaded_file: {uploaded_file}")
        logger.info(f"job_text length: {len(job_text) if job_text else 0}")

        # Validate job description
        if not job_text:
            print("ERROR: No job text provided")
            return JsonResponse({'success': False, 'error': 'Job description is required.'}, status=400)

        # Handle resume input - either selected from account or uploaded file
        resume_text = ""
        
        print(f"=== RESUME VALIDATION ===")
        print(f"selected_resume_id: {selected_resume_id}")
        print(f"uploaded_file: {uploaded_file}")
        
        if selected_resume_id:
            print("Processing selected resume...")
            # Get resume data from the selected resume
            from resume_builder.models import Resume
            try:
                resume = Resume.objects.get(id=selected_resume_id, user=request.user)
                print(f"Found resume: {resume.name}")
                
                # Debug: Log the resume data structure
                print(f"=== DEBUG: Resume Data Structure ===")
                print(f"personal_info: {resume.personal_info}")
                print(f"personal_info keys: {list(resume.personal_info.keys()) if resume.personal_info else []}")
                print(f"full_name from personal_info: '{resume.personal_info.get('full_name', '') if resume.personal_info else ''}'")
                
                # Check for alternative name fields
                personal_info = resume.personal_info or {}
                possible_name_fields = ['full_name', 'name', 'first_name', 'last_name', 'title']
                for field in possible_name_fields:
                    value = personal_info.get(field, '')
                    if value:
                        print(f"Found name in field '{field}': '{value}'")
                
                # Also check the top-level resume data for name fields
                for field in possible_name_fields:
                    value = getattr(resume, field, '')
                    if value:
                        print(f"Found name in top-level field '{field}': '{value}'")
                print(f"=====================================")
                
                # Extract the applicant name from resume data
                applicant_name = ''
                
                # Try multiple possible name fields in order of preference
                name_fields = ['full_name', 'name', 'title']
                for field in name_fields:
                    value = personal_info.get(field, '').strip()
                    if value:
                        applicant_name = value
                        print(f"Found applicant name in '{field}': '{applicant_name}'")
                        break
                
                # If not found in personal_info, check top-level resume data
                if not applicant_name:
                    for field in name_fields:
                        value = getattr(resume, field, '').strip()
                        if value:
                            applicant_name = value
                            print(f"Found applicant name in top-level '{field}': '{applicant_name}'")
                            break
                
                # Fallback to user's name if not found in resume
                if not applicant_name:
                    applicant_name = request.user.get_full_name() or request.user.username
                    print(f"Using fallback name from user: '{applicant_name}'")
                
                print(f"Final applicant name: '{applicant_name}'")
                
                # Build resume text from structured data
                resume_text = f"""
                {personal_info.get('full_name', '')}
                {personal_info.get('current_role', '')}

                Experience:
                {resume.experience}

                Skills:
                {resume.skills}

                Education:
                {resume.education}
                """
                print(f"Resume text length: {len(resume_text)}")
            except Resume.DoesNotExist:
                print(f"ERROR: Resume {selected_resume_id} not found")
                return JsonResponse({'success': False, 'error': 'Selected resume not found.'}, status=400)
        
        elif uploaded_file:
            print("Processing uploaded file...")
            # For uploaded files, let AI extract the name from resume content
            applicant_name = None  # This will trigger AI to extract name from resume
            print(f"Will extract name from uploaded resume content")
            
            # Process uploaded file
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'pdf':
                try:
                    import pdfplumber
                    with pdfplumber.open(uploaded_file) as pdf:
                        resume_text = ""
                        for page in pdf.pages:
                            resume_text += page.extract_text() or ""
                except ImportError:
                    return JsonResponse({
                        'success': False,
                        'error': 'PDF processing is not available. Please upload a TXT file.'
                    }, status=400)
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': f'Error processing PDF file: {str(e)}'
                    }, status=400)
            elif file_extension == 'txt':
                try:
                    resume_text = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        # Fallback to latin-1 if utf-8 fails
                        resume_text = uploaded_file.read().decode('latin-1')
                    except Exception as e:
                        return JsonResponse({
                            'success': False,
                            'error': f'Error reading text file: {str(e)}'
                        }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Unsupported file format. Please upload a PDF or TXT file.'
                }, status=400)
        else:
            print("ERROR: Neither resume selected nor file uploaded")
            return JsonResponse({'success': False, 'error': 'Please either select a resume or upload a file.'}, status=400)

        print(f"=== FINAL VALIDATION ===")
        print(f"resume_text length: {len(resume_text)}")
        print(f"job_text length: {len(job_text) if job_text else 0}")
        print(f"applicant_name: {applicant_name}")
        print(f"=========================")

        # Generate cover letter using the raw text method
        result = generate_cover_letter_from_raw_text(job_text, resume_text, applicant_name)

        if result['success']:
            # Save the cover letter to the database
            cover_letter_obj = CoverLetter.objects.create(
                user=request.user,
                title=f"Cover Letter for {job_text[:50]}..." if len(job_text) > 50 else job_text,
                content=result['cover_letter'],
                job_description=job_text,
                status='completed'
            )
            
            # Store the cover letter in session for the response page
            request.session['generated_cover_letter'] = result['cover_letter']
            request.session['cover_letter_id'] = cover_letter_obj.id
            
            # Redirect to the response page
            return redirect('coverletter:cover_letter_response')
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=500)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def cover_letter_response(request):
    """View to display the generated cover letter response."""
    cover_letter = request.session.get('generated_cover_letter', '')
    cover_letter_id = request.session.get('cover_letter_id')
    
    if not cover_letter:
        return redirect('coverletter:job_cover_letter')
    
    # Get the cover letter object if we have an ID
    cover_letter_obj = None
    if cover_letter_id:
        try:
            cover_letter_obj = CoverLetter.objects.get(id=cover_letter_id, user=request.user)
        except CoverLetter.DoesNotExist:
            pass
    
    context = {
        'cover_letter': cover_letter,
        'cover_letter_obj': cover_letter_obj,
        'page_title': 'Cover Letter Generated',
        'page_description': 'Your AI-generated cover letter is ready!'
    }
    
    return render(request, 'coverletter/cover_letter_response.html', context)

@login_required
def download_cover_letter_pdf(request, cover_letter_id):
    """
    Generates and serves a PDF version of the cover letter.
    
    This function:
    1. Retrieves the cover letter from the database
    2. Parses the structured content (stored as Python dict string)
    3. Extracts user info, employer info, greeting, introduction, and body
    4. Generates a professional PDF using the PDF Generator app
    5. Returns the PDF as a downloadable file
    
    Args:
        request: Django request object
        cover_letter_id: ID of the cover letter to download
        
    Returns:
        HttpResponse: PDF file for download
        
    Raises:
        404: If cover letter not found or user doesn't have access
        500: If PDF generation fails
    """
    import json
    from datetime import datetime
    
    cover_letter = get_object_or_404(CoverLetter, id=cover_letter_id, user=request.user)
    
    # Parse the cover letter content (stored using eval() and str())
    # Note: Content is stored as Python dict string, not JSON
    try:
        # The content is stored as a Python dict string, not JSON
        content_data = eval(cover_letter.content) if cover_letter.content else {}
    except (NameError, SyntaxError, TypeError):
        # Fallback if content is not in expected format
        content_data = {}
    
    # Extract data from the structured content
    # Keys use underscores (user_info, employer_info) not camelCase
    user_info = content_data.get('user_info', {})
    employer_info = content_data.get('employer_info', {})
    greeting = content_data.get('greeting', {})
    introduction = content_data.get('introduction', {})
    body = content_data.get('body', {})
    
    # Prepare context for the template
    # Handle both dict format (from AI) and direct string format
    context = {
        'cover_letter': cover_letter,
        'sender_name': user_info.get('full_name', ''),
        'sender_address': user_info.get('address', ''),
        'sender_email': user_info.get('email', ''),
        'sender_phone': user_info.get('phone', ''),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'recipient_name': employer_info.get('hiring_manager', 'Hiring Manager'),
        'company_name': employer_info.get('company_name', ''),
        'company_address': employer_info.get('company_address', ''),
        'greeting': greeting.get('text', 'Dear Hiring Manager,') if isinstance(greeting, dict) else greeting,
        'introduction': introduction.get('text', '') if isinstance(introduction, dict) else introduction,
        'body': body.get('text', '') if isinstance(body, dict) else body
    }
    
    try:
        # Import PDFGenerator from the PDF Generator app
        from pdf_generator.core.generator import PDFGenerator
        
        # Generate the PDF using the template with optimized settings
        # Format: Letter size with compact margins for single-page layout
        pdf_bytes = PDFGenerator.generate_from_template(
            'coverletter/pdf_template.html',
            context,
            options={
                'format': 'Letter',
                'orientation': 'portrait',
                'margins': {
                    'top': '0.75in',
                    'right': '0.75in',
                    'bottom': '0.75in',
                    'left': '0.75in'
                },
                'print_background': True,
                'prefer_css_page_size': True
            }
        )
        
        # Create the HTTP response with proper headers for download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="cover_letter_{cover_letter.id}.pdf"'
        
        return response
        
    except ImportError:
        # Fallback if PDFGenerator is not available
        logger.error("PDF Generator app not available")
        return HttpResponse(
            "PDF generation is not available. Please contact support.",
            content_type='text/plain',
            status=500
        )
    except Exception as e:
        logger.error(f"Error generating PDF for cover letter {cover_letter_id}: {str(e)}")
        return HttpResponse(
            f"Error generating PDF: {str(e)}",
            content_type='text/plain',
            status=500
        )

@login_required
@require_http_methods(["POST"])
def generate_cover_letter_pdf(request):
    """
    Generate a PDF version of the cover letter from session data.
    """
    try:
        import json
        from datetime import datetime
        
        # Get the edited cover letter content from the request
        data = json.loads(request.body)
        cover_letter_content = data.get('cover_letter', '')
        
        if not cover_letter_content:
            # Fallback to session data if no content provided
            cover_letter_content = request.session.get('generated_cover_letter', '')
        
        if not cover_letter_content:
            return JsonResponse({'success': False, 'error': 'No cover letter content found'}, status=400)
        
        # Save the current content to session (in case it was edited)
        request.session['generated_cover_letter'] = cover_letter_content
        
        # Create context for the template
        context = {
            'cover_letter': cover_letter_content,
        }
        
        # Import PDFGenerator from the PDF Generator app
        from pdf_generator.core.generator import PDFGenerator
        
        # Generate the PDF using the new template
        pdf_bytes = PDFGenerator.generate_from_template(
            'coverletter/cover_letter_pdf.html',
            context,
            options={
                'format': 'Letter',
                'orientation': 'portrait',
                'margins': {
                    'top': '0.75in',
                    'right': '0.75in',
                    'bottom': '0.75in',
                    'left': '0.75in'
                },
                'print_background': True,
                'prefer_css_page_size': True
            }
        )
        
        # Create the HTTP response with proper headers for download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="cover_letter.pdf"'
        
        return response
        
    except ImportError:
        # Fallback if PDFGenerator is not available
        logger.error("PDF Generator app not available")
        return JsonResponse({
            'success': False,
            'error': 'PDF generation is not available. Please contact support.'
        }, status=500)
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error generating PDF: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def edit_cover_letter(request, cover_letter_id):
    """
    API endpoint to edit and save a cover letter.
    
    This endpoint allows users to update their cover letter content
    through a JSON API call.
    
    Args:
        request: Django request object with JSON body
        cover_letter_id: ID of the cover letter to edit
        
    Returns:
        JsonResponse: Success/error status with message
    """
    try:
        cover_letter = get_object_or_404(CoverLetter, id=cover_letter_id, user=request.user)
        
        data = json.loads(request.body)
        new_content = data.get('content')

        if new_content is None:
            return JsonResponse({'status': 'failed', 'error': 'Content is missing.'}, status=400)
            
        cover_letter.content = new_content
        cover_letter.save()
        
        return JsonResponse({'status': 'success', 'message': 'Cover letter updated successfully.'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'failed', 'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        logger.error(f"Error updating cover letter {cover_letter_id}: {str(e)}")
        return JsonResponse({'status': 'failed', 'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def save_edited_content(request):
    """
    Save the edited cover letter content to session and database.
    """
    try:
        import json
        
        # Get the edited content from the request
        data = json.loads(request.body)
        cover_letter_content = data.get('cover_letter', '')
        
        if not cover_letter_content:
            return JsonResponse({'success': False, 'error': 'No cover letter content provided'}, status=400)
        
        # Save to session
        request.session['generated_cover_letter'] = cover_letter_content
        
        # Also update the database record if we have a cover letter ID
        cover_letter_id = request.session.get('cover_letter_id')
        if cover_letter_id:
            try:
                cover_letter_obj = CoverLetter.objects.get(id=cover_letter_id, user=request.user)
                cover_letter_obj.content = cover_letter_content
                cover_letter_obj.save()
            except CoverLetter.DoesNotExist:
                pass  # If the cover letter doesn't exist, just save to session
        
        return JsonResponse({'success': True, 'message': 'Cover letter content saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving edited content: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error saving content: {str(e)}'
        }, status=500)

@login_required
def my_cover_letters(request):
    """View to display all cover letters for the current user"""
    cover_letters = CoverLetter.objects.filter(user=request.user).order_by('-generated_at')
    
    context = {
        'cover_letters': cover_letters,
        'page_title': 'My Cover Letters',
        'page_description': 'View and manage your cover letters'
    }
    
    return render(request, 'coverletter/my_cover_letters.html', context)

@login_required
@require_http_methods(["POST"])
def delete_cover_letter(request, cover_letter_id):
    """Delete a cover letter"""
    try:
        cover_letter = get_object_or_404(CoverLetter, id=cover_letter_id, user=request.user)
        cover_letter.delete()
        return JsonResponse({'success': True, 'message': 'Cover letter deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting cover letter {cover_letter_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Failed to delete cover letter'}, status=500)