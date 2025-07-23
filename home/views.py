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
        'page_description': 'Learn about our mission to revolutionize job applications with AI-powered cover letters.',
        'meta_description': 'Discover how AI Cover Letter is transforming the job application process with intelligent, personalized cover letter generation.'
    }
    return render(request, 'home/about.html', context)

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