from django.urls import path
from . import views  # Import directly from views.py

app_name = 'email_utility'

urlpatterns = [
    # Gmail OAuth endpoints
    path('auth/gmail/', views.gmail_authorize, name='gmail_authorize'),
    path('auth/gmail/callback/', views.gmail_callback, name='gmail_callback'),
    path('auth/yahoo/', views.yahoo_authorize, name='yahoo_authorize'),
    path('auth/yahoo/callback/', views.yahoo_callback, name='yahoo_callback'),
    
    # Email composition and sending
    path('compose/<str:document_type>/<int:document_id>/', views.email_compose, name='email_compose'),
    path('send/', views.send_email, name='send_email'),
    
    # Email history and settings
    path('history/', views.email_history, name='email_history'),
    path('settings/', views.gmail_settings, name='gmail_settings'),
    path('disconnect/', views.disconnect_gmail, name='disconnect_gmail'),
    path('disconnect/yahoo/', views.disconnect_yahoo, name='disconnect_yahoo'),
    path('accounts/connect/', views.connect_smtp_account, name='connect_smtp_account'),
    path('accounts/<int:account_id>/default/', views.set_default_smtp_account, name='set_default_smtp_account'),
    path('accounts/<int:account_id>/disconnect/', views.disconnect_smtp_account, name='disconnect_smtp_account'),
] 