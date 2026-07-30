from django.urls import path

from . import views

app_name = 'automation'

urlpatterns = [
    path('ultimate/setup/', views.ultimate_setup, name='ultimate_setup'),
    path('ultimate/setup/done/', views.ultimate_setup_done, name='ultimate_setup_done'),
    path(
        'ultimate/setup/suggest-titles/',
        views.suggest_title_family,
        name='suggest_title_family',
    ),
]
