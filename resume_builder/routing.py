"""
WebSocket routing configuration for resume_builder app.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/resume-builder/(?P<user_id>\w+)/$', consumers.ResumeBuilderConsumer.as_asgi()),
    re_path(r'ws/resume-builder/$', consumers.ResumeBuilderConsumer.as_asgi()),
] 