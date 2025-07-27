from django.urls import path
from . import views

app_name = 'qa'

urlpatterns = [
    path('test/', views.test_view, name='test'),
    path('load-questions/', views.load_questions_by_category, name='load_questions'),
    path('submit/', views.submit_answers, name='submit_answers'),
    path('api/interview-coach/', views.interview_coach_api, name='interview_coach_api'),
] 