from django.urls import path
from . import views

app_name = 'coverletter'

urlpatterns = [
    path('', views.index, name='index'),
    path('job-cover-letter/', views.job_cover_letter, name='job_cover_letter'),
    path('response/', views.cover_letter_response, name='cover_letter_response'),
    path('view/<int:cover_letter_id>/', views.cover_letter_view, name='cover_letter_view'),
    path('download/<int:cover_letter_id>/', views.download_cover_letter_pdf, name='download_cover_letter_pdf'),
    path('edit/<int:cover_letter_id>/', views.edit_cover_letter, name='edit_cover_letter'),
    path('generate-pdf/', views.generate_cover_letter_pdf, name='generate_cover_letter_pdf'),
    path('save-edited-content/', views.save_edited_content, name='save_edited_content'),
    path('my-cover-letters/', views.my_cover_letters, name='my_cover_letters'),
    path('delete/<int:cover_letter_id>/', views.delete_cover_letter, name='delete_cover_letter'),
] 