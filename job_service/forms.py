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
            'placeholder': 'e.g., Software Engineer, Marketing Manager, Data Analyst'
        }),
        help_text="What type of job are you looking for?"
    )
    
    application_reason = forms.ChoiceField(
        choices=[
            ('career_growth', 'Career Growth & Advancement'),
            ('better_compensation', 'Better Compensation & Benefits'),
            ('work_life_balance', 'Better Work-Life Balance'),
            ('relocation', 'Relocation to New City/Country'),
            ('travel_opportunity', 'Travel & Work Abroad'),
            ('industry_change', 'Change of Industry'),
            ('company_culture', 'Better Company Culture'),
            ('remote_work', 'Remote Work Opportunities'),
            ('other', 'Other')
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
    
    # Step 2: Location Preferences
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., United States, Canada, United Kingdom'
        })
    )
    
    state_province = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., California, Ontario, England'
        })
    )
    
    city_preference = forms.ChoiceField(
        choices=[
            ('specific_city', 'Specific City'),
            ('nearby_cities', 'Nearby Cities (within 50 miles)'),
            ('any_city', 'Any City in State/Province'),
            ('remote_only', 'Remote Only'),
            ('hybrid', 'Hybrid (Some Office Time)')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    specific_city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., San Francisco, Toronto, London'
        })
    )
    
    distance_preference = forms.ChoiceField(
        choices=[
            ('0-25', '0-25 miles'),
            ('25-50', '25-50 miles'),
            ('50-100', '50-100 miles'),
            ('100+', '100+ miles'),
            ('any', 'Any distance')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
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
        
        # Validate city preference
        city_preference = cleaned_data.get('city_preference')
        specific_city = cleaned_data.get('specific_city')
        
        if city_preference == 'specific_city' and not specific_city:
            raise forms.ValidationError("Please specify a city when selecting 'Specific City' option.")
        
        # Validate application reason
        application_reason = cleaned_data.get('application_reason')
        other_reason = cleaned_data.get('other_reason')
        
        if application_reason == 'other' and not other_reason:
            raise forms.ValidationError("Please specify your reason for applying when selecting 'Other'.")
        
        return cleaned_data 