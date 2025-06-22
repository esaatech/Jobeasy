from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('job-applications/', views.job_applications_list, name='job_applications_list'),
    path('api/generate-job-application/', views.generate_job_application, name='generate_job_application'),
    path('api/delete-job-application/<int:job_id>/', views.delete_job_application, name='delete_job_application'),
] 