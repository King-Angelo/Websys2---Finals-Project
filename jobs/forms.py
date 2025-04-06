from django import forms
from .models import JobSeeker, Employer, JobPosting, Application, Skill, Benefit, JobAlert
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Company size choices for employer registration
COMPANY_SIZE_CHOICES = [
    ('1-10', '1-10 employees'),
    ('11-50', '11-50 employees'),
    ('51-200', '51-200 employees'),
    ('201-500', '201-500 employees'),
    ('501-1000', '501-1000 employees'),
    ('1000+', '1000+ employees'),
]

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeeker
        fields = [
            'phone', 'address', 'location', 'education', 'experience', 
            'skills', 'resume', 'profile_picture', 'expected_salary', 
            'preferred_job_types', 'preferred_locations', 'professional_summary'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., New York, NY'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'expected_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50000'}),
            'preferred_job_types': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Full Time, Remote'}),
            'preferred_locations': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., New York, San Francisco'}),
            'professional_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = Employer
        fields = ['company_name', 'company_description', 'industry', 'company_size', 
                 'location', 'website', 'logo']
        widgets = {
            'company_description': forms.Textarea(attrs={'rows': 4}),
        }

class JobPostingForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True
    )
    
    preferred_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False
    )
    
    benefits = forms.ModelMultipleChoiceField(
        queryset=Benefit.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False
    )

    class Meta:
        model = JobPosting
        fields = [
            'title', 'category', 'description', 'requirements', 
            'responsibilities', 'qualifications', 'job_type',
            'experience_level', 'location', 'is_remote',
            'salary_min', 'salary_max', 'is_salary_negotiable',
            'required_skills', 'preferred_skills', 'benefits',
            'deadline', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control'}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control'}),
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        deadline = cleaned_data.get('deadline')

        if salary_min and salary_max and salary_min > salary_max:
            raise ValidationError('Minimum salary cannot be greater than maximum salary')

        if deadline and deadline < timezone.now():
            raise ValidationError('Deadline cannot be in the past')

        return cleaned_data

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ApplicationUpdateForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make resume field optional when updating
        self.fields['resume'].required = False
        # Add help text for resume field
        self.fields['resume'].help_text = 'Leave empty to keep the current resume'

class EmployerRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=100)
    industry = forms.CharField(max_length=100)
    company_size = forms.ChoiceField(choices=COMPANY_SIZE_CHOICES)
    website = forms.URLField(required=False)
    company_description = forms.CharField(widget=forms.Textarea)
    location = forms.CharField(max_length=100)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'company_name', 
                 'industry', 'company_size', 'website', 'company_description', 'location')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Check if user already has an employer profile
            if not hasattr(user, 'employer'):
                employer = Employer.objects.create(
                    user=user,
                    company_name=self.cleaned_data['company_name'],
                    industry=self.cleaned_data['industry'],
                    company_size=self.cleaned_data['company_size'],
                    website=self.cleaned_data['website'],
                    company_description=self.cleaned_data['company_description'],
                    location=self.cleaned_data['location']
                )
            else:
                # Update existing employer profile
                employer = user.employer
                employer.company_name = self.cleaned_data['company_name']
                employer.industry = self.cleaned_data['industry']
                employer.company_size = self.cleaned_data['company_size']
                employer.website = self.cleaned_data['website']
                employer.company_description = self.cleaned_data['company_description']
                employer.location = self.cleaned_data['location']
                employer.save()
                
        return user

class JobSeekerRegistrationForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    location = forms.CharField(max_length=100, required=False)
    education = forms.CharField(widget=forms.Textarea, required=False)
    experience = forms.CharField(widget=forms.Textarea, required=False)
    skills = forms.CharField(widget=forms.Textarea, required=False)
    expected_salary = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    preferred_job_types = forms.CharField(max_length=100, required=False)
    preferred_locations = forms.CharField(max_length=200, required=False)
    professional_summary = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone', 'address', 
                 'location', 'education', 'experience', 'skills', 'expected_salary',
                 'preferred_job_types', 'preferred_locations', 'professional_summary')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Check if user already has a job seeker profile
            if not hasattr(user, 'jobseeker'):
                job_seeker = JobSeeker.objects.create(
                    user=user,
                    phone=self.cleaned_data['phone'],
                    address=self.cleaned_data['address'],
                    location=self.cleaned_data['location'],
                    education=self.cleaned_data['education'],
                    experience=self.cleaned_data['experience'],
                    skills=self.cleaned_data['skills'],
                    expected_salary=self.cleaned_data['expected_salary'],
                    preferred_job_types=self.cleaned_data['preferred_job_types'],
                    preferred_locations=self.cleaned_data['preferred_locations'],
                    professional_summary=self.cleaned_data['professional_summary']
                )
            else:
                # Update existing job seeker profile
                job_seeker = user.jobseeker
                job_seeker.phone = self.cleaned_data['phone']
                job_seeker.address = self.cleaned_data['address']
                job_seeker.location = self.cleaned_data['location']
                job_seeker.education = self.cleaned_data['education']
                job_seeker.experience = self.cleaned_data['experience']
                job_seeker.skills = self.cleaned_data['skills']
                job_seeker.expected_salary = self.cleaned_data['expected_salary']
                job_seeker.preferred_job_types = self.cleaned_data['preferred_job_types']
                job_seeker.preferred_locations = self.cleaned_data['preferred_locations']
                job_seeker.professional_summary = self.cleaned_data['professional_summary']
                job_seeker.save()
                
        return user

class JobAlertForm(forms.ModelForm):
    class Meta:
        model = JobAlert
        fields = [
            'title', 'location', 'job_type', 'industry', 
            'experience_level', 'salary_min', 'salary_max', 
            'skills', 'frequency'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job title keywords'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., New York, NY'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'industry': forms.Select(attrs={'class': 'form-select'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum salary'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum salary'}),
            'skills': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
        }
