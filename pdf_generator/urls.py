"""
PDF Generator URLs

URL patterns for the PDF Generator app.
"""

from django.urls import path
from . import views

app_name = 'pdf_generator'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/generate/', views.generate_pdf_api, name='generate_api'),
    path('generate/', views.PDFGeneratorView.as_view(), name='generate'),
    path('test/', views.test_pdf, name='test'),
] 