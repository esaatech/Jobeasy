from django.urls import path
from . import views
from .views import (
    FAQListAPIView, TestimonialListAPIView, NewsletterSignupCreateAPIView, ContactMessageCreateAPIView
)

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('job-cover-letter/', views.job_cover_letter, name='job_cover_letter'),
    path('api/faqs/', FAQListAPIView.as_view(), name='api-faq-list'),
    path('api/testimonials/', TestimonialListAPIView.as_view(), name='api-testimonial-list'),
    path('api/newsletter/', NewsletterSignupCreateAPIView.as_view(), name='api-newsletter-signup'),
    path('api/contact/', ContactMessageCreateAPIView.as_view(), name='api-contact-message'),
]

