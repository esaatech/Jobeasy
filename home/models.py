from django.db import models

# Create your models here.

class CoverLetterInstruction(models.Model):
    title = models.CharField(max_length=255, default='Default Instructions')
    greeting = models.CharField(max_length=255, default='Start with "Dear Hiring Manager,"')
    focus = models.CharField(max_length=255, default='Focus on relevant experiences')
    understanding = models.CharField(max_length=255, default="Demonstrate clear understanding of the company's needs")
    enthusiasm = models.CharField(max_length=255, default='Show enthusiasm for the role and company')
    examples = models.CharField(max_length=255, default='Include specific examples and achievements')
    tone = models.CharField(max_length=255, default='Maintain a professional yet engaging tone')
    closing = models.CharField(max_length=255, default='End with "Sincerely," followed by the applicant name on a new line')
    no_dates = models.CharField(max_length=255, default='Do not include any dates or addresses')
    length_limit = models.CharField(max_length=255, default='Keep the length to one page maximum.')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
