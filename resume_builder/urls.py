from django.urls import path, re_path
from . import views

app_name = 'resume_builder'

urlpatterns = [
    path('', views.create_resume, name='create_resume'),
    path('create-resume/', views.create_resume, name='create_resume'),
    path('edit-resume/<int:resume_id>/', views.create_resume, name='edit_resume'),
    path('create-resume/submit/', views.create_resume_submit, name='create_resume_submit'),
    path('optimize/', views.optimize_resume, name='optimize_resume'),
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('resume/view/', views.view_resume, name='view_resume'),
    path('resume/view/<int:resume_id>/', views.view_resume, name='view_resume_by_id'),
    path('download/', views.download_resume, name='download_resume'),
    path('preview/<str:template_id>/', views.preview_template, name='preview_template'),
    
    # Subscription check
    path('check-access/', views.check_resume_update_access, name='check_resume_update_access'),
    
    # Step-specific save endpoints
    path('save-personal-info/', views.save_personal_info, name='save_personal_info'),
    path('save-experience/', views.save_experience, name='save_experience'),
    path('save-education/', views.save_education, name='save_education'),
    path('save-skills/', views.save_skills, name='save_skills'),
    path('save-additional/', views.save_additional, name='save_additional'),
    path('finalize-resume/', views.finalize_resume, name='finalize_resume'),
    path('get-resume-content/<int:resume_id>/', views.get_resume_content, name='get_resume_content'),
    path('save-summary/', views.save_summary, name='save_summary'),

    # Misc
    path('save-resume/', views.save_resume, name='save_resume'),
    path('my-resumes/', views.my_resumes, name='my_resumes'),
    path('delete-resume/<int:resume_id>/', views.delete_resume, name='delete_resume'),
    re_path(r'^download/(?P<resume_id>[0-9]+|anonymous)/(?P<format_type>[^/]+)/$', views.download_resume_file, name='download_resume_file'),
    path('switch-template/', views.switch_template, name='switch_template'),
    path('preview-anonymous/', views.preview_anonymous_resume, name='preview_anonymous_resume'),
    path('create-from-data/', views.create_resume_from_data, name='create_resume_from_data'),
    path('create-after-auth/', views.create_resume_after_auth, name='create_resume_after_auth'),
]