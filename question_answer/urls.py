from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_questions, name='qa_test'),
] 