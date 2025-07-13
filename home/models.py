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

class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    published = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en', help_text='Language code, e.g., en, es')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    quote = models.TextField()
    avatar = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    published = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}: {self.quote[:30]}..."

class NewsletterSignup(models.Model):
    email = models.EmailField(unique=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} <{self.email}>"

class JobOpening(models.Model):
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return self.title
