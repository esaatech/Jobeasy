from django.urls import path
from . import views  # Import directly from views.py

app_name = 'email_utility'

urlpatterns = [
    # Existing email configuration URLs...
    
    # Mailbox URLs
    path('mailbox/', views.mailbox_view, name='mailbox'),
    path('mailbox/message/<int:message_id>/', views.message_detail, name='message_detail'),
    path('mailbox/sync/', views.sync_mailbox, name='sync_mailbox'),
    path('email-setup/step1/', views.email_setup_step1, name='email_setup_step1'),
    path('email-setup/step2/<str:provider_id>/', views.email_setup_step2, name='email_setup_step2'),
    path('get-existing-emails/', views.get_existing_emails, name='get_existing_emails'),
    path('email-setup-task-select/', views.email_setup_task_select, name='email_setup_task_select'),
    path('save-email-configuration/', views.save_email_configuration, name='save_email_configuration'),

] 