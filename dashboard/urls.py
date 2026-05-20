from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('job-applications/<int:job_id>/', views.job_application_detail, name='job_application_detail'),
    path('job-applications/', views.job_applications_list, name='job_applications_list'),
    path('api/evaluate-job-fit/', views.evaluate_job_fit, name='evaluate_job_fit'),
    path('api/generate-job-application/', views.generate_job_application, name='generate_job_application'),
    path('api/delete-job-application/<int:job_id>/', views.delete_job_application, name='delete_job_application'),
] 