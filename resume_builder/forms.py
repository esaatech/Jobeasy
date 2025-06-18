from django import forms
from .models import Resume

class ResumeForm(forms.ModelForm):
    # Personal Information Fields
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    location = forms.CharField(max_length=100)
    
    # Professional Summary
    summary = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Write a brief summary of your professional background and career objectives'
        }),
        required=False
    )

    class Meta:
        model = Resume
        fields = [
            'original_content',
            'job_description',
            # Remove 'title' if it's here
            # Add only fields that exist in your Resume model
        ]

    def clean(self):
        cleaned_data = super().clean()
        
        # Structure the data into JSON format
        personal_info = {
            'full_name': cleaned_data.get('full_name'),
            'email': cleaned_data.get('email'),
            'phone': cleaned_data.get('phone'),
            'location': cleaned_data.get('location'),
        }

        # Add the structured data back to cleaned_data
        cleaned_data['personal_info'] = personal_info
        cleaned_data['summary'] = cleaned_data.get('summary', '')
        cleaned_data['work_experience'] = []  # Will be populated from form submission
        cleaned_data['education'] = []  # Will be populated from form submission
        cleaned_data['skills'] = {
            'technical': [],
            'soft': []
        }  # Will be populated from form submission

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set JSON fields
        instance.personal_info = self.cleaned_data['personal_info']
        instance.summary = self.cleaned_data['summary']
        instance.work_experience = self.cleaned_data['work_experience']
        instance.education = self.cleaned_data['education']
        instance.skills = self.cleaned_data['skills']

        if commit:
            instance.save()
        return instance
