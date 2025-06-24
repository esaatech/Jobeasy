from django.urls import path
from . import views

app_name = 'coverletter'

urlpatterns = [
    path('', views.index, name='index'),
    path('job-cover-letter/', views.job_cover_letter, name='job_cover_letter'),
    path('view/<int:cover_letter_id>/', views.cover_letter_view, name='cover_letter_view'),
    path('download/<int:cover_letter_id>/', views.download_cover_letter_pdf, name='download_cover_letter_pdf'),
    path('edit/<int:cover_letter_id>/', views.edit_cover_letter, name='edit_cover_letter'),
] 