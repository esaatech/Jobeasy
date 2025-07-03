from django.urls import path
from . import views

app_name = 'job_service'

urlpatterns = [
    # Main service page
    path('', views.job_application_service, name='job_application_service'),
    
    # User dashboard and management
    path('dashboard/', views.job_dashboard, name='dashboard'),
    path('preferences/', views.user_preferences, name='preferences'),
    
    # Job browsing and searching
    path('jobs/', views.job_listings, name='job_listings'),
    path('jobs/<uuid:job_id>/', views.job_detail, name='job_detail'),
    
    # Job applications
    path('jobs/<uuid:job_id>/apply/', views.apply_to_job, name='apply_to_job'),
    path('applications/', views.application_tracking, name='application_tracking'),
    path('applications/<int:application_id>/update/', views.update_application_status, name='update_application_status'),
    path('interview-prep/', views.interview_prep, name='interview_prep'),
] 