from django.db import models
from django.conf import settings

# Create your models here.

class CoverLetter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cover_letters')
    # Add any other fields you may need for the cover letter
    # For now, this is enough to get the count
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cover Letter for {self.user.username} created on {self.created_at.strftime('%Y-%m-%d')}"
