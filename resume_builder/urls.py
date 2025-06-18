from django.urls import path
from . import views

app_name = 'resume_builder'

urlpatterns = [
    path('', views.resume_home, name='home'),
    path('create-resume/', views.create_resume, name='create_resume'),
    path('create-resume/submit/', views.create_resume_submit, name='create_resume_submit'),
    path('optimize/', views.optimize_resume, name='optimize_resume'),
    path('download/', views.download_resume, name='download_resume'),
    
    path('save-resume/', views.save_resume, name='save_resume'),
    path('switch-template/', views.switch_template, name='switch_template'),
]