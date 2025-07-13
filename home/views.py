from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .cover_letter import generate_cover_letter_from_fields, generate_cover_letter_from_raw_text
import logging
from rest_framework import generics
from .models import FAQ, Testimonial, NewsletterSignup, ContactMessage
from .serializers import FAQSerializer, TestimonialSerializer, NewsletterSignupSerializer, ContactMessageSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Get the logger for this app
logger = logging.getLogger('home')

# Create your views here.
def index(request):
    return render(request, 'home/home.html')   

def about(request):
    context = {
        'page_title': 'About Us - AI Cover Letter',
        'page_description': 'Learn about our mission to revolutionize job applications with AI',
        'meta_description': 'Discover how AI Cover Letter is transforming the job application process with intelligent resume and cover letter generation.',
    }
    return render(request, 'home/about.html', context)

@require_http_methods(["GET", "POST"])
def job_cover_letter(request):
    if request.method == "GET":
        context = {
            'page_title': 'Cover Letter AI',
            'page_description': 'Generate a professional cover letter using AI',
            'meta_description': 'Create a customized cover letter instantly with our AI-powered tool.',
        }
        return render(request, 'tools/job_cover_letter.html', context)
    
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

def contact(request):
    context = {
        'page_title': 'Contact Us - AI Cover Letter',
        'page_description': 'Get in touch with our team for support, feedback, or partnership inquiries.'
    }
    return render(request, 'home/contact.html', context)

def careers(request):
    from .models import JobOpening
    jobs = JobOpening.objects.filter(is_active=True)
    context = {
        'page_title': 'Careers - AI Cover Letter',
        'page_description': 'Join our team and help revolutionize the job application process!',
        'jobs': jobs
    }
    return render(request, 'home/careers.html', context)

def terms(request):
    return render(request, 'home/terms.html', {
        'page_title': 'Terms & Conditions - AI Cover Letter',
        'page_description': 'Read our terms and conditions.'
    })

def privacy(request):
    return render(request, 'home/privacy.html', {
        'page_title': 'Privacy Policy - AI Cover Letter',
        'page_description': 'Read our privacy policy.'
    })

# API: List all published FAQs
class FAQListAPIView(generics.ListAPIView):
    queryset = FAQ.objects.filter(published=True)
    serializer_class = FAQSerializer

# API: List all published Testimonials
class TestimonialListAPIView(generics.ListAPIView):
    queryset = Testimonial.objects.filter(published=True)
    serializer_class = TestimonialSerializer

# API: Create Newsletter Signup
@method_decorator(csrf_exempt, name='dispatch')
class NewsletterSignupCreateAPIView(generics.CreateAPIView):
    queryset = NewsletterSignup.objects.all()
    serializer_class = NewsletterSignupSerializer

# API: Create Contact Message
@method_decorator(csrf_exempt, name='dispatch')
class ContactMessageCreateAPIView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer