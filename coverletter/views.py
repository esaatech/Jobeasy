from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .cover_letter import generate_cover_letter_from_fields, generate_cover_letter_from_raw_text
from .models import CoverLetter
from pdf_generator.core.generator import PDFGenerator
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
        'cover_letter': cover_letter,
        'hero_content': {
            'page_title': cover_letter.title,
        }
    }
    
    return render(request, 'coverletter/cover_letter_view.html', context)

@require_http_methods(["GET", "POST"])
def job_cover_letter(request):
    if request.method == "GET":
        context = {
            'page_title': 'Cover Letter AI',
            'page_description': 'Generate a professional cover letter using AI',
            'meta_description': 'Create a customized cover letter instantly with our AI-powered tool.',
        }
        return render(request, 'coverletter/job_cover_letter.html', context)
    
    try:
        data = request.POST
        input_method = data.get('input_method')
        job_input_method = data.get('job_input_method')

        # Handle resume input
        if input_method == 'manual':
            candidate_details = {
                'full_name': data.get('full_name'),
                'current_role': data.get('current_role'),
                'experience': data.get('experience'),
                'key_skills': data.get('key_skills'),
                'achievements': data.get('achievements')
            }
            resume_text = f"""
            {candidate_details['full_name']}
            {candidate_details['current_role']}

            Experience:
            {candidate_details['experience']}

            Achievements:
            {candidate_details['achievements']}

            Skills:
            {candidate_details['key_skills']}
            """
        else:  # upload
            resume_file = request.FILES.get('resume')
            if not resume_file:
                return JsonResponse({'success': False, 'error': 'Resume file is required.'}, status=400)
            
            # Get file extension
            file_extension = resume_file.name.split('.')[-1].lower()
            
            if file_extension == 'pdf':
                try:
                    import pdfplumber
                    with pdfplumber.open(resume_file) as pdf:
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
                    resume_text = resume_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        # Fallback to latin-1 if utf-8 fails
                        resume_text = resume_file.read().decode('latin-1')
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

        # Handle job input
        if job_input_method == 'structured':
            job_details = {
                'position': data.get('position'),
                'company': data.get('company'),
                'department': data.get('department'),
                'description': data.get('description')
            }
            job_text = f"""
            Position: {job_details['position']}
            Company: {job_details['company']}
            Department: {job_details['department']}
            
            Description:
            {job_details['description']}
            """
        else:  # unstructured
            job_text = data.get('job_posting')
            if not job_text:
                return JsonResponse({'success': False, 'error': 'Job posting is required.'}, status=400)

        # Generate cover letter based on input combination
        if input_method == 'manual' and job_input_method == 'structured':
            result = generate_cover_letter_from_fields(job_details, candidate_details)
        else:
            result = generate_cover_letter_from_raw_text(job_text, resume_text)

        if result['success']:
            formatted_letter = result['cover_letter'].replace('\n', '<br>')
            return JsonResponse({
                'success': True,
                'cover_letter': formatted_letter,
            })
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
def download_cover_letter_pdf(request, cover_letter_id):
    """Generates and serves a PDF version of the cover letter."""
    cover_letter = get_object_or_404(CoverLetter, id=cover_letter_id, user=request.user)
    
    context = {'cover_letter': cover_letter}
    
    # Generate the PDF using the dedicated template
    pdf_bytes = PDFGenerator.generate_from_template(
        'coverletter/pdf_template.html',
        context,
        options={
            'format': 'A4',
            'filename': f'cover_letter_{cover_letter.id}.pdf'
        }
    )
    
    # Create the HTTP response
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cover_letter_{cover_letter.id}.pdf"'
    
    return response

@login_required
@require_http_methods(["POST"])
def edit_cover_letter(request, cover_letter_id):
    """API endpoint to edit and save a cover letter."""
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