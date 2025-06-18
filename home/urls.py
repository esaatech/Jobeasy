from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('job-cover-letter/', views.job_cover_letter, name='job_cover_letter'),
]

