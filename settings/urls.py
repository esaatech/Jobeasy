from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_root, name='dashboard'),
    path('profile/', views.profile_settings, name='profile'),
    path('notifications/', views.notification_settings, name='notifications'),
    path('integrations/', views.integration_settings, name='integrations'),
    path('integrations/gmail/', views.gmail_settings, name='gmail_settings'),
    path('billing/', views.billing_settings, name='billing'),
    path('billing/add-payment-method/', views.add_payment_method, name='add_payment_method'),
    path('billing/download-invoices/', views.download_invoices, name='download_invoices'),
    path('billing/update-auto-renewal/', views.update_auto_renewal, name='update_auto_renewal'),
    path('billing/cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    path('security/', views.security_settings, name='security'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
] 