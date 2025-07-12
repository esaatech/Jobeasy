from django import forms
from django.contrib.auth.models import User
from resume_builder.models import Resume
from .models import UserJobPreferences

class JobApplicationForm(forms.Form):
    """Form for the complete job application process"""
    
    # Step 1: Job Details
    job_title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., Software Engineer, Marketing Manager, Data Analyst',
            'data-i18n-placeholder': 'job_title_placeholder'
        }),
        help_text="What type of job are you looking for?"
    )
    
    application_reason = forms.ChoiceField(
        choices=[
            ('career_growth', 'career_growth'),
            ('better_compensation', 'better_compensation'),
            ('work_life_balance', 'work_life_balance'),
            ('relocation', 'relocation'),
            ('travel_opportunity', 'travel_opportunity'),
            ('industry_change', 'industry_change'),
            ('company_culture', 'company_culture'),
            ('remote_work', 'remote_work'),
            ('other', 'other')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        help_text="Why are you applying for this job?"
    )
    
    other_reason = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Please specify your reason for applying...'
        })
    )
    
    # New location fields
    countries = forms.CharField(widget=forms.HiddenInput(), required=False)
    work_arrangements = forms.CharField(widget=forms.HiddenInput(), required=False)
    city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter city name'
        })
    )
    distance = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Distance in miles'
        })
    )
    # Deprecated/legacy fields (keep for compatibility, but not required)
    country = forms.CharField(required=False, widget=forms.HiddenInput())
    state_province = forms.CharField(required=False, widget=forms.HiddenInput())
    city_preference = forms.CharField(required=False, widget=forms.HiddenInput())
    specific_city = forms.CharField(required=False, widget=forms.HiddenInput())
    distance_preference = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_countries(self):
        import json
        data = self.cleaned_data.get('countries')
        if not data:
            return []
        try:
            countries = json.loads(data)
            return countries
        except Exception:
            raise forms.ValidationError("Invalid country/state data.")

    def clean_work_arrangements(self):
        import json
        data = self.cleaned_data.get('work_arrangements')
        if not data:
            return []
        try:
            work_arrangements = json.loads(data)
            return work_arrangements
        except Exception:
            raise forms.ValidationError("Invalid work arrangement data.")

    # Step 3: Contact Information
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'your.email@example.com'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '+1 (555) 123-4567'
        })
    )
    
    preferred_contact_method = forms.ChoiceField(
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('both', 'Both')
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'contact-method'
        })
    )
    
    # Additional Preferences
    salary_expectations = forms.ChoiceField(
        choices=[
            ('negotiable', 'Negotiable'),
            ('market_rate', 'Market Rate'),
            ('specific_range', 'Specific Range')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    salary_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '50000'
        })
    )
    
    salary_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '80000'
        })
    )
    
    start_date = forms.ChoiceField(
        choices=[
            ('immediately', 'Immediately'),
            ('2_weeks', '2 Weeks'),
            ('1_month', '1 Month'),
            ('2_months', '2 Months'),
            ('3_months', '3 Months'),
            ('flexible', 'Flexible')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    additional_notes = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 4,
            'placeholder': 'Any additional information about your preferences, requirements, or special circumstances...'
        })
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No need to populate resume choices since we removed that step
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate salary range
        salary_expectations = cleaned_data.get('salary_expectations')
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_expectations == 'specific_range':
            if not salary_min or not salary_max:
                raise forms.ValidationError("Please specify both minimum and maximum salary for specific range.")
            if salary_min >= salary_max:
                raise forms.ValidationError("Minimum salary must be less than maximum salary.")
        
        # Validate city
        city = cleaned_data.get('city')
        if not city:
            raise forms.ValidationError("Please enter a city.")
        
        # Validate application reason
        application_reason = cleaned_data.get('application_reason')
        other_reason = cleaned_data.get('other_reason')
        
        if application_reason == 'other' and not other_reason:
            raise forms.ValidationError("Please specify your reason for applying when selecting 'Other'.")
        
        return cleaned_data 