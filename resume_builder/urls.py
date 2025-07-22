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
    
    # AI Assistant
    path('ai-assistant/', views.ai_resume_assistant, name='ai_resume_assistant'),
    path('api/chat/', views.chat_with_ai, name='chat_with_ai'),
    path('api/resumes/', views.get_user_resumes, name='get_user_resumes'),
    path('api/resume/<int:resume_id>/preview/', views.get_resume_preview, name='get_resume_preview'),
    
    # Dynamic Tab Content Endpoints
    path('api/resume-list-tab/', views.resume_list_tab, name='resume_list_tab'),
    path('api/cover-letter-tab/', views.cover_letter_tab, name='cover_letter_tab'),
    path('api/templates-tab/', views.templates_tab, name='templates_tab'),
    
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

    # AI summary generation endpoint
    path('generate-ai-summary/', views.generate_ai_summary, name='generate_ai_summary'),

    # Misc
    path('save-resume/', views.save_resume, name='save_resume'),
    path('my-resumes/', views.my_resumes, name='my_resumes'),
    path('delete-resume/<int:resume_id>/', views.delete_resume, name='delete_resume'),
    re_path(r'^download/(?P<resume_id>[0-9]+|anonymous)/(?P<format_type>[^/]+)/$', views.download_resume_file, name='download_resume_file'),
    path('switch-template/', views.switch_template, name='switch_template'),
    path('preview-anonymous/', views.preview_anonymous_resume, name='preview_anonymous_resume'),
    path('create-from-data/', views.create_resume_from_data, name='create_resume_from_data'),
    path('create-after-auth/', views.create_resume_after_auth, name='create_resume_after_auth'),
    path('templates/', views.get_available_templates, name='get_available_templates'),





    #test
    path('test-resumes/', views.test_resumes, name='test_resumes'),
]