from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Generic subscription purchase flow
    path('purchase/<int:plan_id>/', 
        views.PlanPurchaseView.as_view(), 
        name='plan_purchase'
    ),
    
    # Process payment
    path('process-payment/<int:plan_id>/<int:duration_id>/',
        views.process_payment,
        name='process_payment'
    ),
    
    # Success page
    path('success/<int:subscription_id>/',
        views.checkout_success,
        name='checkout_success'
    ),
    path('cancel/', views.cancel_subscription, name='cancel_subscription'),

    # pricing page
    path('pricing/', views.pricing, name='pricing'),

    path('test-dialogs/', views.test_subscription_dialogs, name='test_dialogs'),
] 