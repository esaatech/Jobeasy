from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_dashboard, name='dashboard'),
    path('profile/', views.profile_settings, name='profile'),
    path('notifications/', views.notification_settings, name='notifications'),
    path('integrations/', views.integration_settings, name='integrations'),
    path('billing/', views.billing_settings, name='billing'),
    path('security/', views.security_settings, name='security'),
    path('delete-account/', views.delete_account, name='delete_account'),
] 