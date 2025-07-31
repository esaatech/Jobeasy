from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class JobSource(models.Model):
    """Represents different job sources (websites, APIs, etc.)"""
    name = models.CharField(max_length=100)
    url = models.URLField()
    source_type = models.CharField(max_length=50, choices=[
        ('website', 'Website Scraping'),
        ('api', 'API Integration'),
        ('manual', 'Manual Entry'),
        ('rss', 'RSS Feed')
    ])
    is_active = models.BooleanField(default=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.source_type})"

class Job(models.Model):
    """Represents a job posting"""
    job_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=50, choices=[
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance')
    ])
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    description = models.TextField()
    requirements = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    application_url = models.URLField()
    source = models.ForeignKey(JobSource, on_delete=models.CASCADE, related_name='jobs')
    external_id = models.CharField(max_length=100, blank=True)  # ID from external source
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_curated = models.BooleanField(default=False)  # Manually curated by team
    tags = models.JSONField(default=list)  # Skills, technologies, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title', 'company']),
            models.Index(fields=['location']),
            models.Index(fields=['job_type']),
            models.Index(fields=['is_active', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company}"

class JobApplication(models.Model):
    """
    JOB SERVICE JobApplication Model
    
    This model is used for tracking job applications to jobs found through the job
    scraping service. It's different from dashboard.models.JobApplication.
    
    Key Differences from dashboard JobApplication:
    - Purpose: Track applications to scraped jobs (not manual job application creation)
    - Job Reference: Uses ForeignKey to Job model (not string job_name)
    - Cover Letter: Uses TextField 'cover_letter_used' (not ForeignKey to CoverLetter model)
    - Resume: Uses ForeignKey to Resume model (same as dashboard)
    - Status: Detailed application tracking (applied, under_review, interviewed, etc.)
    - Related Name: 'job_applications' (to avoid conflicts with dashboard)
    
    Usage: When users apply to jobs found through the job scraping service
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=50, choices=[
        ('applied', 'Applied'),
        ('under_review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('offer_received', 'Offer Received'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn')
    ], default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    resume_used = models.ForeignKey('resume_builder.Resume', on_delete=models.SET_NULL, null=True, blank=True)
    cover_letter_used = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'job']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.job.title}"

class UserJobPreferences(models.Model):
    """User preferences for job matching"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_preferences')
    preferred_locations = models.JSONField(default=list)
    preferred_job_types = models.JSONField(default=list)
    preferred_salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_industries = models.JSONField(default=list)
    required_skills = models.JSONField(default=list)
    preferred_skills = models.JSONField(default=list)
    remote_preference = models.CharField(max_length=20, choices=[
        ('remote_only', 'Remote Only'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-site'),
        ('any', 'Any')
    ], default='any')
    notification_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('never', 'Never')
    ], default='weekly')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"

class JobScrapingLog(models.Model):
    """Logs for job scraping activities"""
    source = models.ForeignKey(JobSource, on_delete=models.CASCADE, related_name='scraping_logs')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    jobs_found = models.IntegerField(default=0)
    jobs_added = models.IntegerField(default=0)
    jobs_updated = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='running')
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.source.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"

class ServicePackage(models.Model):
    """Service packages for job application service"""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    features = models.JSONField(default=list)
    max_applications = models.IntegerField(null=True, blank=True)  # null = unlimited
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ${self.price}"

class UserSubscription(models.Model):
    """User subscriptions to service packages"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_service_subscriptions')
    package = models.ForeignKey(ServicePackage, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending')
    ], default='pending')
    applications_used = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.package.name}"

class InterviewPrepSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_sessions')
    job_role = models.CharField(max_length=100, blank=True)
    job_description = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_score = models.FloatField(default=0)
    max_score = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.job_role or 'Custom'} ({self.started_at.date()})"

class InterviewQuestion(models.Model):
    session = models.ForeignKey(InterviewPrepSession, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Q{self.order} for {self.session}"

class InterviewAnswer(models.Model):
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE, related_name='answers')
    user_answer = models.TextField()
    ai_feedback = models.TextField(blank=True)
    score = models.FloatField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.question} (Score: {self.score})"

class JobApplicationRequest(models.Model):
    """Complete job application service request"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_application_requests')
    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Job Details
    job_title = models.CharField(max_length=200)
    application_reason = models.CharField(max_length=50, choices=[
        ('career_growth', 'Career Growth & Advancement'),
        ('better_compensation', 'Better Compensation & Benefits'),
        ('work_life_balance', 'Better Work-Life Balance'),
        ('relocation', 'Relocation to New City/Country'),
        ('travel_opportunity', 'Travel & Work Abroad'),
        ('industry_change', 'Change of Industry'),
        ('company_culture', 'Better Company Culture'),
        ('remote_work', 'Remote Work Opportunities'),
        ('other', 'Other')
    ])
    other_reason = models.TextField(blank=True)
    
    # Resume Information
    resume_used = models.ForeignKey('resume_builder.Resume', on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_resume = models.FileField(upload_to='job_applications/resumes/', null=True, blank=True)
    
    # Location Preferences (new fields)
    countries = models.JSONField(default=list, blank=True, null=True, help_text="List of selected countries and states")
    city = models.CharField(max_length=100, blank=True, help_text="User-entered city name")
    distance = models.IntegerField(blank=True, null=True, help_text="Distance preference in miles")
    work_arrangements = models.JSONField(default=list, blank=True, null=True, help_text="List of preferred work arrangements (remote, hybrid, onsite)")
    # Deprecated/legacy fields (keep for compatibility)
    country = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    city_preference = models.CharField(max_length=20, blank=True)
    specific_city = models.CharField(max_length=100, blank=True)
    distance_preference = models.CharField(max_length=20, blank=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    preferred_contact_method = models.CharField(max_length=10, choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('both', 'Both')
    ])
    
    # Additional Preferences
    salary_expectations = models.CharField(max_length=20, choices=[
        ('negotiable', 'Negotiable'),
        ('market_rate', 'Market Rate'),
        ('specific_range', 'Specific Range')
    ])
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.CharField(max_length=20, choices=[
        ('immediately', 'Immediately'),
        ('2_weeks', '2 Weeks'),
        ('1_month', '1 Month'),
        ('2_months', '2 Months'),
        ('3_months', '3 Months'),
        ('flexible', 'Flexible')
    ])
    additional_notes = models.TextField(blank=True)
    
    # Status and Processing
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    
    # Results
    jobs_found = models.IntegerField(default=0)
    applications_submitted = models.IntegerField(default=0)
    interviews_scheduled = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Processing details
    processing_notes = models.TextField(blank=True)
    ai_optimization_applied = models.BooleanField(default=False)
    cover_letters_generated = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['job_title']),
            models.Index(fields=['country', 'state_province']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.job_title} ({self.status})"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_processing(self):
        return self.status == 'processing'
    
    @property
    def can_cancel(self):
        return self.status in ['pending', 'processing']
    
    def get_location_display(self):
        """Get formatted location string"""
        location_parts = [self.country, self.state_province]
        if self.specific_city:
            location_parts.insert(1, self.specific_city)
        return ', '.join(location_parts)
    
    def get_salary_display(self):
        """Get formatted salary string"""
        if self.salary_expectations == 'specific_range' and self.salary_min and self.salary_max:
            return f"${self.salary_min:,.0f} - ${self.salary_max:,.0f}"
        return self.get_salary_expectations_display()
