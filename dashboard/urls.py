from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('job-applications/', views.job_applications_list, name='job_applications_list'),
] 