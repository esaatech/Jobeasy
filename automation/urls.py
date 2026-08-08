from django.urls import path

from . import views
from . import views_ops

app_name = 'automation'

urlpatterns = [
    path('ultimate/setup/', views.ultimate_setup, name='ultimate_setup'),
    path('ultimate/setup/done/', views.ultimate_setup_done, name='ultimate_setup_done'),
    path(
        'ultimate/setup/suggest-titles/',
        views.suggest_title_family,
        name='suggest_title_family',
    ),
    path('locations/countries/', views.locations_countries, name='locations_countries'),
    path(
        'locations/countries/<str:code>/regions/',
        views.locations_regions,
        name='locations_regions',
    ),
    path(
        'ops/matched-tasks/<int:task_id>/',
        views_ops.matched_task_ops,
        name='matched_task_ops',
    ),
]
