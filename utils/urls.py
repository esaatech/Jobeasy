from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    # Add any utility-related URLs here if needed
    # For now, this is mainly for static files and templates
    path('alert-demo/', views.alert_demo, name='alert_demo'),
] 