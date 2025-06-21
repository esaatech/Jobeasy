from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from .models import Resume
from .forms import ResumeForm
import json
from pydantic import BaseModel, Field
from typing import List
import os
import tempfile
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
from dotenv import load_dotenv
from django.urls import reverse
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
import uuid
from django.template.loader import render_to_string
from django.utils import timezone

# Import libraries for file processing
import PyPDF2
from docx import Document

# Load environment variables from .env file
load_dotenv()

class OptimizedResume(BaseModel):
    optimized_content: str = Field(description="The ATS-optimized resume content")
    keyword_matches: List[str] = Field(description="List of important keywords matched from job description")
    improvement_suggestions: List[str] = Field(description="List of suggestions for improving the resume")
    ats_score: int = Field(description="ATS compatibility score out of 100")

class ResumeOptimizer:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def optimize(self, resume_text: str, job_description: str) -> OptimizedResume:
        """
        Simple mock optimization that provides basic improvements
        In a real implementation, this would use OpenAI API or other AI service
        """
        
        # Extract some keywords from job description (simple approach)
        job_words = job_description.lower().split()
        common_keywords = ['python', 'javascript', 'react', 'node', 'aws', 'docker', 'kubernetes', 
                          'agile', 'scrum', 'leadership', 'management', 'development', 'engineering']
        
        found_keywords = [word for word in common_keywords if word in job_words]
        
        # Create a simple optimized version
        optimized_content = f"""
{resume_text}

--- OPTIMIZATION SUGGESTIONS ---
• Enhanced with relevant keywords: {', '.join(found_keywords[:5])}
• Improved formatting for ATS compatibility
• Added action verbs and quantifiable achievements
• Structured content for better readability
        """.strip()
        
        # Generate improvement suggestions
        suggestions = [
            "Add more quantifiable achievements (e.g., 'Increased performance by 25%')",
            "Include relevant keywords from the job description",
            "Use action verbs at the beginning of bullet points",
            "Ensure consistent formatting throughout",
            "Add a professional summary section"
        ]
        
        # Calculate a mock ATS score
        ats_score = min(85 + len(found_keywords) * 2, 95)
        
        return OptimizedResume(
            optimized_content=optimized_content,
            keyword_matches=found_keywords,
            improvement_suggestions=suggestions,
            ats_score=ats_score
        )

def create_resume(request, resume_id=None):
    """
    Handles both creating a new resume and editing an existing one.
    If resume_id is provided, it fetches the existing resume (draft or ready).
    Otherwise, it prepares for a new resume.
    """
    resume_instance = None
    if resume_id:
        resume_instance = get_object_or_404(Resume, id=resume_id, user=request.user)

    # Generate default resume name only if creating a new resume
    default_name = ""
    if not resume_instance:
        base_name = "My Resume"
        counter = 1
        default_name = base_name
        
        if request.user.is_authenticated:
            existing_names = list(request.user.resumes.values_list('name', flat=True))
            while default_name in existing_names:
                counter += 1
                default_name = f"{base_name} {counter}"
    
    # Hero section content
    hero_content = {
        'title': 'Resume Builder & Optimizer',
        'description': 'Create or optimize your ATS-friendly resume with our professional templates and AI-powered suggestions. Stand out to employers and increase your chances of getting hired.',
        'buttons': {
            'create': 'Create New Resume',
            'optimize': 'Optimize Existing Resume'
        },
        'credits_text': ''
    }

    context = {
        'form': ResumeForm(),
        'hero_content': hero_content,
        'resume_services': {
            'builder_cost': 10  # or whatever the cost is
        },
        'default_resume_name': default_name,
        'resume_instance': resume_instance
    }

    return render(request, 'resume_builder/resume.html', context)

@login_required
def optimize_resume(request):
    if request.method == 'POST':
        try:
            # Debug logging
            logger.debug(f"Form data: {request.POST}")
            logger.debug(f"Files: {request.FILES}")

            resume_text = ""
            resume_file = request.FILES.get('resume_file')
            
            if resume_file:
                logger.info(f"Processing file: {resume_file.name}")
                # Get file extension
                file_extension = os.path.splitext(resume_file.name)[1].lower()
                
                # Create a temporary file to handle the upload
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in resume_file.chunks():
                        temp_file.write(chunk)
                
                try:
                    # Process different file types
                    if file_extension == '.pdf':
                        logger.info("Processing PDF file")
                        with open(temp_file.name, 'rb') as file:
                            pdf_reader = PyPDF2.PdfReader(file)
                            for page in pdf_reader.pages:
                                resume_text += page.extract_text()
                    elif file_extension in ['.doc', '.docx']:
                        logger.info("Processing Word document")
                        doc = Document(temp_file.name)
                        resume_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                    else:
                        raise ValueError(f"Unsupported file type: {file_extension}")
                except Exception as e:
                    logger.error(f"File processing error: {str(e)}")
                    raise
                finally:
                    # Clean up the temporary file
                    os.unlink(temp_file.name)
            else:
                logger.info("Using text input")
                resume_text = request.POST.get('resume_text', '').strip()

            if not resume_text:
                logger.error("No resume content provided")
                raise ValueError("Please provide either a resume file or paste resume text")

            job_description = request.POST.get('job_description', '').strip()
            if not job_description:
                logger.error("No job description provided")
                raise ValueError("Please provide a job description")

            logger.info("Starting resume optimization")
            optimizer = ResumeOptimizer(api_key=os.getenv('OPENAI_API_KEY'))
            optimization_result = optimizer.optimize(resume_text, job_description)
            logger.info("Resume optimization completed")

            # Store optimization results in session
            request.session['optimization_results'] = {
                'original_content': resume_text,
                'optimized_content': optimization_result.optimized_content,
                'job_description': job_description,
                'keyword_matches': optimization_result.keyword_matches,
                'improvement_suggestions': optimization_result.improvement_suggestions,
                'ats_score': optimization_result.ats_score,
                'is_new': True  # Flag to indicate this is not saved yet
            }

            return JsonResponse({
                'success': True,
                'message': 'Resume optimized successfully',
                'redirect_url': reverse('resume_builder:view_resume')
            })

        except ValueError as ve:
            logger.warning(f"Validation error: {str(ve)}")
            return JsonResponse({
                'success': False,
                'error': str(ve)
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f"An error occurred: {str(e)}"
            }, status=400)
    
    # GET request
    hero_content = {
        'page_title': 'Optimize Your Resume',
        'page_description': 'Upload your resume and job description to create an ATS-optimized version tailored to the position.'
    }
    return render(request, 'resume_builder/optimize_resume.html', {'hero_content': hero_content})

@login_required
def view_resume(request, resume_id=None):
    """
    Display a resume by rendering the template dynamically from database data.
    If resume_id is provided, it fetches a saved resume and renders it with the chosen template.
    Otherwise, it uses unsaved optimization results from the session.
    """
    context = {}
    if resume_id:
        # Viewing a saved resume
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        
        # Prepare resume data for template rendering
        resume_data = {
            'personal_info': resume.personal_info or {},
            'experience': resume.experience or [],
            'education': resume.education or [],
            'skills': resume.skills or {},
            'additional': resume.additional or {}
        }
        
        # Get the template ID (default to professional if not set)
        template_id = resume.template_id or 'professional'
        
        # Render the resume with the chosen template
        html_content = render_to_string(f'resume_templates/{template_id}.html', {'resume_data': resume_data})
        
        # Create full HTML document
        full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{resume.personal_info.get('full_name', 'Resume')} - Resume</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {{
            body {{{{ margin: 0; padding: 20px; }}}}
            .professional-template, .modern-template, .creative-template {{{{
                max-width: none; box-shadow: none;
            }}}}
        }}
    </style>
</head>
<body class="bg-white">
    {html_content}
</body>
</html>
"""
        
        context = {
            'resume_html': full_html,
            'resume': resume,
            'hero_content': {
                'page_title': f'Resume: {resume.name}',
                'page_description': 'View your resume below. You can edit, save, or download it.'
            }
        }
        
        return render(request, 'resume_builder/view_resume.html', context)
    else:
        # Viewing a newly optimized, unsaved resume (legacy support)
        resume_data = request.session.get('optimization_results')
        if not resume_data:
            return redirect('resume_builder:optimize_resume')
        
        context = {
            'resume_data': resume_data,
            'hero_content': {
                'page_title': 'Optimization Results',
                'page_description': 'Review your resume below. You can edit, save, or download it.'
            }
        }
        
        return render(request, 'resume_builder/view_resume.html', context)

@login_required
def download_resume(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '')

            # Create a new Word document
            doc = Document()
            doc.add_heading('Optimized Resume', 0)

            for paragraph in content.split('\n'):
                if paragraph.strip():
                    doc.add_paragraph(paragraph.strip())

            # Save to BytesIO instead of temporary file
            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)

            # For direct download
            response = HttpResponse(
                doc_io.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = 'attachment; filename=optimized_resume.docx'
            return response

        except Exception as e:
            logger.error(f"Word generation error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    # GET request - Get resume data from session
    resume_data = request.session.get('resume_data')
    if not resume_data:
        return redirect('resume_builder:create_resume')
    
    # Available templates with descriptive IDs
    templates = [
        {'id': 'professional', 'name': 'Professional'},
        {'id': 'modern', 'name': 'Modern'},
        {'id': 'creative', 'name': 'Creative'},
    ]
    
    # Get active template (default to professional)
    active_template = request.session.get('active_template', 'professional')
    
    context = {
        'resume_data': resume_data,
        'templates': templates,
        'active_template': active_template,
        'selected_template': f'resume_templates/{active_template}.html'
    }
    
    return render(request, 'download_resume.html', context)

@login_required
def switch_template(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_id = data.get('template_id')
            
            # Update valid template IDs
            if template_id not in ['professional', 'modern', 'creative']:
                raise ValueError('Invalid template ID')
            
            # Store selected template in session
            request.session['active_template'] = template_id
            
            # Render the selected template with resume data
            resume_data = request.session.get('resume_data')
            return render(request, f'resume_templates/{template_id}.html', {'resume_data': resume_data})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def preview_template(request, template_id):
    """Preview template with sample data - optimized for multi-country/multi-language support"""
    if template_id not in ['professional', 'modern', 'creative']:
        return JsonResponse({'error': 'Invalid template ID'}, status=400)
    
    # Get user's locale from request (could be from user preferences, Accept-Language header, etc.)
    user_locale = request.GET.get('locale', 'en-US')  # Default to US English
    
    # Sample resume data - optimized for internationalization
    # In production, this would come from a database or translation files
    sample_resume_data = get_localized_sample_data(user_locale)
    
    context = {'resume_data': sample_resume_data}
    return render(request, f'resume_templates/{template_id}.html', context)

def get_localized_sample_data(locale='en-US'):
    """Get sample resume data based on locale - supports multi-country/multi-language"""
    
    # Sample data templates for different locales
    sample_data_templates = {
        'en-US': {
            'personal_info': {
                'full_name': 'Sarah Johnson',
                'title': 'Senior Software Engineer',
                'email': 'sarah.johnson@email.com',
                'phone': '(555) 123-4567',
                'summary': 'Experienced software engineer with 5+ years developing scalable web applications. Passionate about clean code, user experience, and emerging technologies.'
            },
            'experience': [
                {
                    'company': 'TechCorp Inc.',
                    'position': 'Senior Software Engineer',
                    'startDate': '2022-01',
                    'endDate': 'Present',
                    'description': 'Led development of microservices architecture serving 1M+ users. Mentored junior developers and implemented CI/CD pipelines.'
                },
                {
                    'company': 'StartupXYZ',
                    'position': 'Full Stack Developer',
                    'startDate': '2020-03',
                    'endDate': '2021-12',
                    'description': 'Built and maintained React/Node.js applications. Collaborated with design team to implement responsive UI components.'
                }
            ],
            'education': [
                {
                    'institution': 'University of Technology',
                    'degree': 'Bachelor of Computer Science',
                    'startDate': '2016-09',
                    'endDate': '2020-05',
                    'description': 'Graduated with honors. Specialized in software engineering and database systems.'
                }
            ],
            'skills': {
                'technical': ['JavaScript', 'React', 'Node.js', 'Python', 'PostgreSQL', 'AWS'],
                'soft': ['Leadership', 'Problem Solving', 'Team Collaboration', 'Communication'],
                'languages': ['English', 'Spanish']
            },
            'additional': {
                'certifications': 'AWS Certified Developer, Google Cloud Professional',
                'projects': 'Open-source contributor to React ecosystem, Built personal finance tracker app'
            }
        },
        'es-ES': {
            'personal_info': {
                'full_name': 'María García López',
                'title': 'Ingeniera de Software Senior',
                'email': 'maria.garcia@email.com',
                'phone': '+34 612 345 678',
                'summary': 'Ingeniera de software experimentada con más de 5 años desarrollando aplicaciones web escalables. Apasionada por el código limpio, la experiencia de usuario y las tecnologías emergentes.'
            },
            'experience': [
                {
                    'company': 'TechCorp España',
                    'position': 'Ingeniera de Software Senior',
                    'startDate': '2022-01',
                    'endDate': 'Presente',
                    'description': 'Dirigí el desarrollo de arquitectura de microservicios que sirve a más de 1M de usuarios. Mentoré a desarrolladores junior e implementé pipelines de CI/CD.'
                }
            ],
            'education': [
                {
                    'institution': 'Universidad Politécnica de Madrid',
                    'degree': 'Grado en Ingeniería Informática',
                    'startDate': '2016-09',
                    'endDate': '2020-05',
                    'description': 'Graduada con honores. Especializada en ingeniería de software y sistemas de bases de datos.'
                }
            ],
            'skills': {
                'technical': ['JavaScript', 'React', 'Node.js', 'Python', 'PostgreSQL', 'AWS'],
                'soft': ['Liderazgo', 'Resolución de Problemas', 'Colaboración en Equipo', 'Comunicación'],
                'languages': ['Español', 'Inglés']
            },
            'additional': {
                'certifications': 'Desarrollador Certificado AWS, Profesional de Google Cloud',
                'projects': 'Contribuidora de código abierto al ecosistema React, Construí aplicación de seguimiento financiero personal'
            }
        },
        'fr-FR': {
            'personal_info': {
                'full_name': 'Sophie Martin',
                'title': 'Ingénieure Logiciel Senior',
                'email': 'sophie.martin@email.com',
                'phone': '+33 1 23 45 67 89',
                'summary': 'Ingénieure logiciel expérimentée avec plus de 5 ans de développement d\'applications web évolutives. Passionnée par le code propre, l\'expérience utilisateur et les technologies émergentes.'
            },
            'experience': [
                {
                    'company': 'TechCorp France',
                    'position': 'Ingénieure Logiciel Senior',
                    'startDate': '2022-01',
                    'endDate': 'Présent',
                    'description': 'J\'ai dirigé le développement d\'une architecture de microservices desservant plus d\'1M d\'utilisateurs. J\'ai encadré des développeurs juniors et implémenté des pipelines CI/CD.'
                }
            ],
            'education': [
                {
                    'institution': 'École Centrale Paris',
                    'degree': 'Master en Informatique',
                    'startDate': '2016-09',
                    'endDate': '2020-05',
                    'description': 'Diplômée avec mention. Spécialisée en génie logiciel et systèmes de bases de données.'
                }
            ],
            'skills': {
                'technical': ['JavaScript', 'React', 'Node.js', 'Python', 'PostgreSQL', 'AWS'],
                'soft': ['Leadership', 'Résolution de Problèmes', 'Collaboration d\'Équipe', 'Communication'],
                'languages': ['Français', 'Anglais']
            },
            'additional': {
                'certifications': 'Développeur Certifié AWS, Professionnel Google Cloud',
                'projects': 'Contributeur open source à l\'écosystème React, Construit une application de suivi financier personnel'
            }
        }
    }
    
    # Return localized data or fallback to US English
    return sample_data_templates.get(locale, sample_data_templates['en-US'])

def resume_home(request):
    return render(request, 'resume_builder/resume.html')

@login_required
def save_resume(request):
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                resume_id = data.get('resume_id')

                if resume_id:
                    # Find existing resume and update it
                    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
                    message = 'Changes saved successfully!'
                else:
                    # Create a new resume instance
                    resume = Resume(user=request.user)
                    message = 'Optimized resume saved successfully!'

                # Update the resume object with data from the request
                resume.optimized_content = data.get('content', '')
                resume.job_description = data.get('job_description', '')
                resume.ats_score = data.get('ats_score', 0)
                resume.keyword_matches = data.get('keyword_matches', [])
                resume.improvement_suggestions = data.get('improvement_suggestions', [])
                resume.template_id = data.get('template_id', 'professional')
                
                # After updating content, we must regenerate the HTML file
                from django.template.loader import render_to_string
                from django.core.files.base import ContentFile
                
                resume_template_data = {
                    'personal_info': {
                        'full_name': f'Resume #{resume.id}' if resume.id else 'Optimized Resume',
                        'title': 'ATS-Optimized Version',
                        'email': '', 'phone': '',
                        'summary': resume.optimized_content
                    },
                    'experience': [], 'education': [],
                    'skills': {'technical': resume.keyword_matches, 'soft': [], 'languages': []},
                    'additional': {
                        'certifications': f'ATS Score: {resume.ats_score}/100',
                        'projects': 'Optimized for Applicant Tracking Systems'
                    }
                }
                
                html_content = render_to_string(f'resume_templates/{resume.template_id}.html', {'resume_data': resume_template_data})
                
                full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Optimized Resume</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {{
            body {{{{ margin: 0; padding: 20px; }}}}
            .professional-template, .modern-template, .creative-template {{{{
                max-width: none; box-shadow: none;
            }}}}
        }}
    </style>
</head>
<body class="bg-white">
    {html_content}
</body>
</html>
"""
                file_content = ContentFile(full_html.encode('utf-8'))
                
                # Save the resume object first to ensure it has an ID
                if not resume.id:
                    resume.save()

                # Now save the file with a name that includes the ID
                resume.pdf_file.save(f'optimized_resume_{resume.id}.html', file_content, save=True)

                return JsonResponse({
                    'success': True,
                    'message': message,
                    'resume_id': resume.id
                })
            else:
                # Handle PDF file upload (existing functionality)
                pdf_file = request.FILES.get('pdf_file')
                template_id = request.POST.get('template_id')
                
                if not pdf_file:
                    return JsonResponse({'success': False, 'error': 'PDF file is required'})
                
                # Save the PDF file with default values for required fields
                resume = Resume.objects.create(
                    user=request.user,
                    pdf_file=pdf_file,
                    template_id=template_id,
                    original_content='',
                    optimized_content='',
                    job_description='',
                    ats_score=0,
                    keyword_matches=[],
                    improvement_suggestions=[]
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Resume PDF saved successfully!',
                    'resume_id': resume.id
                })
            
        except Exception as e:
            logger.error(f"Save resume error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def create_resume_submit(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from request
            data = json.loads(request.body)
            
            # Store resume data in session for template rendering
            request.session['resume_data'] = {
                'personal_info': {
                    'full_name': data.get('fullName'),
                    'title': data.get('title'),
                    'email': data.get('email'),
                    'phone': data.get('phone'),
                    'summary': data.get('summary')
                },
                'experience': data.get('experience', []),
                'education': data.get('education', []),
                'skills': {
                    'technical': data.get('technicalSkills', '').split(','),
                    'soft': data.get('softSkills', '').split(','),
                    'languages': data.get('languages', '').split(',')
                },
                'additional': {
                    'certifications': data.get('certifications'),
                    'projects': data.get('projects')
                }
            }

            return JsonResponse({
                'success': True,
                'message': 'Resume created successfully',
                'redirect_url': reverse('resume_builder:download_resume')
            })

        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Resume creation error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to create resume'
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)

@login_required
def my_resumes(request):
    """List all resumes for the current user, with ready resumes first."""
    resumes = request.user.resumes.all().order_by('draft', '-updated_at')
    
    context = {
        'resumes': resumes,
        'hero_content': {
            'page_title': 'My Resumes',
            'page_description': 'Manage and view all your saved resumes.'
        }
    }
    
    return render(request, 'resume_builder/my_resumes.html', context)

@login_required
def delete_resume(request, resume_id):
    """Delete a resume and its associated file"""
    if request.method == 'POST':
        try:
            # Get the resume and ensure it belongs to the current user
            resume = get_object_or_404(Resume, id=resume_id, user=request.user)
            
            # Delete the resume (this will also delete the file due to the model's delete method)
            resume.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Resume deleted successfully!'
            })
            
        except Resume.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Resume not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Delete resume error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to delete resume'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)

@login_required
def download_resume_file(request, resume_id, format_type='html'):
    """Download a resume in the specified format - generates files on-the-fly from database data"""
    try:
        # Get the resume and ensure it belongs to the current user
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        
        # Prepare resume data for template rendering
        resume_data = {
            'personal_info': resume.personal_info or {},
            'experience': resume.experience or [],
            'education': resume.education or [],
            'skills': resume.skills or {},
            'additional': resume.additional or {}
        }
        
        # Get the template ID (default to professional if not set)
        template_id = resume.template_id or 'professional'
        
        if format_type == 'html':
            # Render the resume with the chosen template
            html_content = render_to_string(f'resume_templates/{template_id}.html', {'resume_data': resume_data})
            
            # Create full HTML document
            full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{resume.personal_info.get('full_name', 'Resume')} - Resume</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {{
            body {{{{ margin: 0; padding: 20px; }}}}
            .professional-template, .modern-template, .creative-template {{{{
                max-width: none; box-shadow: none;
            }}}}
        }}
    </style>
</head>
<body class="bg-white">
    {html_content}
</body>
</html>
"""
            # Return HTML directly
            response = HttpResponse(full_html, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="resume_{resume_id}.html"'
            return response
                
        elif format_type == 'pdf':
            # Use the new standalone PDF Generator app
            try:
                from pdf_generator.core.generator import PDFGenerator
                
                # Create context for the resume template
                context = {
                    'resume_data': resume_data,
                    'resume_name': resume.name,
                    'generated_date': timezone.now().strftime('%B %d, %Y')
                }
                
                # Generate PDF using the standalone PDF generator
                pdf_bytes = PDFGenerator.generate_from_template(
                    template_name=f'resume_templates/{template_id}.html',
                    context=context,
                    options={
                        'format': 'A4',
                        'print_background': True,
                        'margins': {
                            'top': '0.5in',
                            'right': '0.5in',
                            'bottom': '0.5in',
                            'left': '0.5in'
                        }
                    }
                )
                
                response = HttpResponse(pdf_bytes, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="resume_{resume_id}.pdf"'
                return response
                
            except ImportError:
                # Fallback to xhtml2pdf if PDF generator is not available
                logger.warning("PDF Generator app not available, falling back to xhtml2pdf")
                from xhtml2pdf import pisa
                
                # Render the resume with the chosen template
                html_content = render_to_string(f'resume_templates/{template_id}.html', {'resume_data': resume_data})
                
                # Create full HTML document
                full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{resume.personal_info.get('full_name', 'Resume')} - Resume</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {{
            body {{{{ margin: 0; padding: 20px; }}}}
            .professional-template, .modern-template, .creative-template {{{{
                max-width: none; box-shadow: none;
            }}}}
        }}
    </style>
</head>
<body class="bg-white">
    {html_content}
</body>
</html>
"""
                pdf_buffer = BytesIO()
                
                pisa_status = pisa.CreatePDF(
                    full_html,
                    dest=pdf_buffer
                )
                
                if pisa_status.err:
                    return HttpResponse(f'We had some errors <pre>{full_html}</pre>')

                pdf_buffer.seek(0)
                
                response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="resume_{resume_id}.pdf"'
                return response
                
        elif format_type == 'word':
            # Convert HTML to Word document using html2docx
            try:
                from html2docx import html2docx
                
                # Render the resume with the chosen template
                html_content = render_to_string(f'resume_templates/{template_id}.html', {'resume_data': resume_data})
                
                # Create full HTML document
                full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{resume.personal_info.get('full_name', 'Resume')} - Resume</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
    {html_content}
</body>
</html>
"""
                docx_buffer = html2docx(full_html, title=f"Resume - {resume.name}")

                response = HttpResponse(
                    docx_buffer.getvalue(), 
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                response['Content-Disposition'] = f'attachment; filename="resume_{resume_id}.docx"'
                return response
                
            except ImportError:
                logger.error("html2docx not available for Word document generation")
                return JsonResponse({'error': 'Word document generation not available'}, status=500)
        
        else:
            return JsonResponse({'error': 'Invalid format'}, status=400)
            
    except Exception as e:
        logger.error(f"Download resume error: {str(e)}")
        return JsonResponse({'error': 'Failed to download resume'}, status=500)

@login_required
def save_personal_info(request):
    """Save step 1: Personal Information and create or update resume"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resume_id = data.get('resume_id')
            is_editing_save = data.get('is_editing_save', False)

            if resume_id:
                # Update existing resume
                resume = get_object_or_404(Resume, id=resume_id, user=request.user)
            else:
                # Create new draft resume
                resume = Resume.objects.create(
                    user=request.user,
                    name=data.get('resume_name', 'My Resume'),
                    draft=True,
                    template_id='professional'
                )
            
            # Update data
            resume.name = data.get('resume_name', resume.name)
            resume.personal_info = {
                'full_name': data.get('fullName'),
                'title': data.get('title'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'summary': data.get('summary')
            }
            resume.save()

            if is_editing_save:
                return JsonResponse({
                    'success': True,
                    'message': 'Personal information saved.',
                    'redirect_url': reverse('resume_builder:my_resumes')
                })
            
            return JsonResponse({
                'success': True,
                'message': 'Personal information saved successfully!',
                'resume_id': resume.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Save personal info error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Failed to save personal information'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
def save_experience(request):
    """Save step 2: Work Experience"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resume_id = data.get('resume_id')
            is_editing_save = data.get('is_editing_save', False)
            
            if not resume_id:
                return JsonResponse({'success': False, 'error': 'Resume ID is required'}, status=400)
            
            resume = get_object_or_404(Resume, id=resume_id, user=request.user)
            resume.experience = data.get('experience', [])
            resume.save()
            
            if is_editing_save:
                return JsonResponse({
                    'success': True,
                    'message': 'Experience saved.',
                    'redirect_url': reverse('resume_builder:my_resumes')
                })

            return JsonResponse({'success': True, 'message': 'Experience saved successfully!'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Save experience error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Failed to save experience'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
def save_education(request):
    """Save step 3: Education"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resume_id = data.get('resume_id')
            is_editing_save = data.get('is_editing_save', False)

            if not resume_id:
                return JsonResponse({'success': False, 'error': 'Resume ID is required'}, status=400)
            
            resume = get_object_or_404(Resume, id=resume_id, user=request.user)
            resume.education = data.get('education', [])
            resume.save()
            
            if is_editing_save:
                return JsonResponse({
                    'success': True,
                    'message': 'Education saved.',
                    'redirect_url': reverse('resume_builder:my_resumes')
                })

            return JsonResponse({'success': True, 'message': 'Education saved successfully!'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Save education error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Failed to save education'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
def save_skills(request):
    """Save step 4: Skills"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resume_id = data.get('resume_id')
            is_editing_save = data.get('is_editing_save', False)

            if not resume_id:
                return JsonResponse({'success': False, 'error': 'Resume ID is required'}, status=400)
            
            resume = get_object_or_404(Resume, id=resume_id, user=request.user)
            resume.skills = {
                'technical': [skill.strip() for skill in data.get('technicalSkills', '').split(',') if skill.strip()],
                'soft': [skill.strip() for skill in data.get('softSkills', '').split(',') if skill.strip()],
                'languages': [lang.strip() for lang in data.get('languages', '').split(',') if lang.strip()]
            }
            resume.save()
            
            if is_editing_save:
                return JsonResponse({
                    'success': True,
                    'message': 'Skills saved.',
                    'redirect_url': reverse('resume_builder:my_resumes')
                })

            return JsonResponse({'success': True, 'message': 'Skills saved successfully!'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Save skills error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Failed to save skills'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
def save_additional(request):
    """Save step 5: Additional Information"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resume_id = data.get('resume_id')
            is_editing_save = data.get('is_editing_save', False)
            
            if not resume_id:
                return JsonResponse({'success': False, 'error': 'Resume ID is required'}, status=400)
            
            resume = get_object_or_404(Resume, id=resume_id, user=request.user)
            resume.additional = {
                'certifications': data.get('certifications'),
                'projects': data.get('projects')
            }
            resume.save()
            
            if is_editing_save:
                return JsonResponse({
                    'success': True,
                    'message': 'Additional info saved.',
                    'redirect_url': reverse('resume_builder:my_resumes')
                })

            return JsonResponse({'success': True, 'message': 'Additional information saved successfully!'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Save additional error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Failed to save additional information'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@login_required
def finalize_resume(request):
    """Finalize resume with template - no longer generates HTML files"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resume_id = data.get('resume_id')
            action = data.get('action', 'save')  # 'save' or 'preview'
            
            if not resume_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Resume ID is required'
                }, status=400)
            
            resume = get_object_or_404(Resume, id=resume_id, user=request.user)
            
            # Update template
            template_id = data.get('template_id', 'professional')
            resume.template_id = template_id
            
            # Set draft to False
            resume.draft = False
            resume.save()
            
            if action == 'save':
                return JsonResponse({
                    'success': True,
                    'message': 'Resume saved successfully!',
                    'redirect_url': reverse('resume_builder:my_resumes')
                })
            else:  # action == 'preview'
                return JsonResponse({
                    'success': True,
                    'message': 'Resume created successfully',
                    'redirect_url': reverse('resume_builder:view_resume_by_id', args=[resume.id])
                })
            
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Finalize resume error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to finalize resume'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)