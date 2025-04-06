from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ckeditor.fields import RichTextField

class JobSeeker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_job_types = models.CharField(max_length=100, blank=True)
    preferred_locations = models.CharField(max_length=200, blank=True)
    professional_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Employer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    company_description = models.TextField()
    industry = models.CharField(max_length=100)
    company_size = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

class JobCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Job Categories"

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Benefit(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For FontAwesome icons

    def __str__(self):
        return self.name

class JobPosting(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('manager', 'Manager'),
    ]

    INDUSTRY_CHOICES = [
        ('tech', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE)
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True)
    description = RichTextField(null=True, blank=True)
    requirements = RichTextField(null=True, blank=True)
    responsibilities = RichTextField(null=True, blank=True)
    qualifications = RichTextField(null=True, blank=True)

    # Job Details
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='entry')
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, default='other')
    location = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_remote = models.BooleanField(default=False)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    is_salary_negotiable = models.BooleanField(default=False)

    # Skills and Benefits
    required_skills = models.ManyToManyField(Skill, related_name='required_jobs')
    preferred_skills = models.ManyToManyField(Skill, related_name='preferred_jobs', blank=True)
    benefits = models.ManyToManyField(Benefit, blank=True)

    # Metadata
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField()
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.salary_max < self.salary_min:
            raise ValidationError('Maximum salary cannot be less than minimum salary')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['deadline']),
            models.Index(fields=['is_active']),
            models.Index(fields=['job_type']),
            models.Index(fields=['location']),
            models.Index(fields=['industry']),
            models.Index(fields=['experience_level']),
        ]

    def save(self, *args, **kwargs):
        # Geocode location if provided
        if self.location and not (self.latitude and self.longitude):
            try:
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user_agent="job_portal")
                location = geolocator.geocode(self.location)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
            except Exception as e:
                print(f"Geocoding error: {e}")
        
        self.clean()
        super().save(*args, **kwargs)

    def calculate_distance(self, lat, lon):
        """Calculate distance from given coordinates using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2
        
        if not all([self.latitude, self.longitude, lat, lon]):
            return None
            
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(lat), radians(lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE)
    applicant = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='applications/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['job', 'applicant']

    def __str__(self):
        return f"{self.applicant.user.username}'s application for {self.job.title}"

class SavedJob(models.Model):
    job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['job_seeker', 'job']

    def __str__(self):
        return f"{self.job_seeker.user.username} saved {self.job.title}"

class JobAlert(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('instant', 'Instant'),
    ]

    job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    job_type = models.CharField(max_length=20, choices=JobPosting.JOB_TYPE_CHOICES, blank=True)
    industry = models.CharField(max_length=50, choices=JobPosting.INDUSTRY_CHOICES, blank=True)
    experience_level = models.CharField(max_length=20, choices=JobPosting.EXPERIENCE_LEVEL_CHOICES, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.job_seeker.user.username}'s alert for {self.title or 'all jobs'}"

    def get_matching_jobs(self):
        """Get jobs matching the alert criteria"""
        jobs = JobPosting.objects.filter(is_active=True)
        
        if self.title:
            jobs = jobs.filter(title__icontains=self.title)
        if self.location:
            jobs = jobs.filter(location__icontains=self.location)
        if self.job_type:
            jobs = jobs.filter(job_type=self.job_type)
        if self.industry:
            jobs = jobs.filter(industry=self.industry)
        if self.experience_level:
            jobs = jobs.filter(experience_level=self.experience_level)
        if self.salary_min:
            jobs = jobs.filter(salary_min__gte=self.salary_min)
        if self.salary_max:
            jobs = jobs.filter(salary_max__lte=self.salary_max)
        if self.skills.exists():
            jobs = jobs.filter(required_skills__in=self.skills.all()).distinct()
            
        # Only return jobs created after the last check
        if self.last_checked:
            jobs = jobs.filter(created_at__gt=self.last_checked)
            
        return jobs.order_by('-created_at')
