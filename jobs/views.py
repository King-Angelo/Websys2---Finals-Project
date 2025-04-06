from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, DeleteView, View
from django.urls import reverse_lazy
from django.db.models import Count, Q
from .models import JobPosting, JobSeeker, Employer, Application, SavedJob, Skill, JobAlert
from .forms import JobSeekerProfileForm, EmployerProfileForm, JobPostingForm, ApplicationForm, EmployerRegistrationForm, JobSeekerRegistrationForm, JobAlertForm, ApplicationUpdateForm
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login

# Create your views here.

class JobListView(ListView):
    model = JobPosting
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        queryset = JobPosting.objects.filter(is_active=True)
        
        # Basic filters
        title = self.request.GET.get('title')
        location = self.request.GET.get('location')
        job_type = self.request.GET.get('job_type')
        salary_min = self.request.GET.get('salary_min')
        salary_max = self.request.GET.get('salary_max')
        industry = self.request.GET.get('industry')
        experience_level = self.request.GET.get('experience_level')
        skills = self.request.GET.getlist('skills')
        radius = self.request.GET.get('radius')
        user_lat = self.request.GET.get('latitude')
        user_lon = self.request.GET.get('longitude')

        if title:
            queryset = queryset.filter(title__icontains=title)
        
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        if salary_min:
            queryset = queryset.filter(salary_min__gte=salary_min)
        
        if salary_max:
            queryset = queryset.filter(salary_max__lte=salary_max)
            
        if industry:
            queryset = queryset.filter(industry=industry)
            
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)
            
        if skills:
            queryset = queryset.filter(required_skills__name__in=skills).distinct()
            
        # Location-based search with radius
        if all([radius, user_lat, user_lon]):
            try:
                radius = float(radius)
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                
                # Filter jobs within radius
                nearby_jobs = []
                for job in queryset:
                    if job.latitude and job.longitude:
                        distance = job.calculate_distance(user_lat, user_lon)
                        if distance and distance <= radius:
                            nearby_jobs.append(job.id)
                
                queryset = queryset.filter(id__in=nearby_jobs)
            except (ValueError, TypeError):
                pass

        return queryset.select_related('employer').prefetch_related('required_skills', 'benefits').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter choices to context
        context['job_types'] = JobPosting.JOB_TYPE_CHOICES
        context['experience_levels'] = JobPosting.EXPERIENCE_LEVEL_CHOICES
        context['industries'] = JobPosting.INDUSTRY_CHOICES
        context['skills'] = Skill.objects.all()
        
        # Add current filter values to context
        context['current_filters'] = {
            'title': self.request.GET.get('title', ''),
            'location': self.request.GET.get('location', ''),
            'job_type': self.request.GET.get('job_type', ''),
            'salary_min': self.request.GET.get('salary_min', ''),
            'salary_max': self.request.GET.get('salary_max', ''),
            'industry': self.request.GET.get('industry', ''),
            'experience_level': self.request.GET.get('experience_level', ''),
            'skills': self.request.GET.getlist('skills', []),
            'radius': self.request.GET.get('radius', ''),
        }
        
        return context

class JobDetailView(DetailView):
    model = JobPosting
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has applied for this job
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'jobseeker'):
                context['has_applied'] = Application.objects.filter(
                    job=self.object,
                    applicant=self.request.user.jobseeker
                ).exists()
                
                # Check if user has saved this job
                context['has_saved'] = SavedJob.objects.filter(
                    job=self.object,
                    job_seeker=self.request.user.jobseeker
                ).exists()
                context['is_jobseeker'] = True
            elif hasattr(self.request.user, 'employer'):
                context['is_employer'] = True
                context['can_edit'] = self.object.employer == self.request.user.employer
        
        # Get similar jobs
        context['similar_jobs'] = JobPosting.objects.filter(
            is_active=True,
            job_type=self.object.job_type,
            location=self.object.location
        ).exclude(
            pk=self.object.pk
        )[:3]
        
        return context

class JobPostingCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'jobs/job_posting_form.html'
    success_url = reverse_lazy('jobs:job_list')

    def form_valid(self, form):
        form.instance.employer = self.request.user.employer
        return super().form_valid(form)

    def test_func(self):
        return hasattr(self.request.user, 'employer')

class JobSeekerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/jobseeker_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_seeker = self.request.user.jobseeker
        
        # Get recent applications
        context['recent_applications'] = Application.objects.filter(
            applicant=job_seeker
        ).order_by('-applied_at')[:5]
        
        # Get saved jobs
        context['saved_jobs'] = SavedJob.objects.filter(
            job_seeker=job_seeker
        ).order_by('-saved_at')[:5]
        
        # Get job alerts
        context['job_alerts'] = JobAlert.objects.filter(
            job_seeker=job_seeker
        ).order_by('-created_at')[:5]
        
        # Get recommended jobs based on skills and salary expectations
        recommended_jobs = JobPosting.objects.filter(is_active=True)
        
        # Only filter by salary if expected_salary is set
        if job_seeker.expected_salary:
            recommended_jobs = recommended_jobs.filter(
                salary_min__lte=job_seeker.expected_salary,
                salary_max__gte=job_seeker.expected_salary
            )
        
        # Order by creation date and limit to 5
        context['recommended_jobs'] = recommended_jobs.order_by('-created_at')[:5]
        
        return context

class SavedJobView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SavedJob
    template_name = 'jobs/savedjob_form.html'
    fields = ['notes']
    success_url = reverse_lazy('jobs:job_list')

    def test_func(self):
        return hasattr(self.request.user, 'jobseeker')

    def form_valid(self, form):
        job = get_object_or_404(JobPosting, pk=self.kwargs['job_id'])
        
        # Check if job is already saved
        if SavedJob.objects.filter(
            job_seeker=self.request.user.jobseeker,
            job=job
        ).exists():
            messages.warning(self.request, 'You have already saved this job.')
            return redirect('jobs:job_detail', pk=job.pk)
            
        form.instance.job_seeker = self.request.user.jobseeker
        form.instance.job = job
        messages.success(self.request, 'Job saved successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['job_id'])
        return context

class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'jobs/application_form.html'
    success_url = reverse_lazy('jobs:jobseeker_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['job_id'])
        return context

    def form_valid(self, form):
        # Check if user has already applied
        if Application.objects.filter(
            job_id=self.kwargs['job_id'],
            applicant=self.request.user.jobseeker
        ).exists():
            messages.error(self.request, 'You have already applied for this job.')
            return redirect('jobs:job_detail', pk=self.kwargs['job_id'])

        form.instance.applicant = self.request.user.jobseeker
        form.instance.job = get_object_or_404(JobPosting, pk=self.kwargs['job_id'])
        return super().form_valid(form)

class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = 'jobs/application_detail.html'
    context_object_name = 'application'

    def get_queryset(self):
        return Application.objects.filter(
            Q(applicant=self.request.user.jobseeker) | 
            Q(job__employer=self.request.user.employer)
        )

class ApplicationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Application
    form_class = ApplicationUpdateForm
    template_name = 'jobs/application_form.html'
    success_url = reverse_lazy('jobs:application_detail')

    def test_func(self):
        application = self.get_object()
        return application.applicant.user == self.request.user

    def get_success_url(self):
        return reverse('jobs:application_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # Only update resume if a new one is provided
        if not form.cleaned_data['resume']:
            form.instance.resume = self.get_object().resume
        return super().form_valid(form)

class ApplicationStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Application
    fields = ['status']
    template_name = 'jobs/application_status_update.html'
    
    def test_func(self):
        application = self.get_object()
        return application.job.employer == self.request.user.employer
    
    def get_success_url(self):
        return reverse_lazy('jobs:employer_dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, f'Application status updated to {form.instance.get_status_display()}')
        return super().form_valid(form)

class EmployerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'jobs/employer_dashboard.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'employer')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employer = self.request.user.employer
        
        # Debug print statements
        print(f"\nDEBUG: Current Employer Details:")
        print(f"Username: {self.request.user.username}")
        print(f"Company Name: {employer.company_name}")
        print(f"Employer ID: {employer.id}")
        
        # Get active job postings for display
        active_jobs = JobPosting.objects.filter(
            employer=employer,
            is_active=True
        ).order_by('-created_at')
        context['active_jobs'] = active_jobs[:5]
        
        # Debug print statements for jobs
        print("\nDEBUG: Active Jobs:")
        for job in active_jobs:
            print(f"- {job.title} (ID: {job.id})")
        
        # Get all applications for this employer
        applications = Application.objects.filter(
            job__employer=employer  # This ensures we get applications for jobs owned by this employer
        ).select_related('job', 'applicant', 'applicant__user').order_by('-applied_at')
        
        # Debug print statements for applications
        print("\nDEBUG: Applications found:")
        for app in applications:
            print(f"- Application ID: {app.id}")
            print(f"  Job: {app.job.title}")
            print(f"  Status: {app.status}")
            print(f"  Applicant: {app.applicant.user.username}")
        
        # Pass all applications to the template
        context['recent_applications'] = applications
        
        # Get application statistics
        context['application_stats'] = {
            'total': applications.count(),
            'pending': applications.filter(status='pending').count(),
            'reviewed': applications.filter(status='reviewed').count(),
            'shortlisted': applications.filter(status='shortlisted').count(),
            'rejected': applications.filter(status='rejected').count(),
            'accepted': applications.filter(status='accepted').count(),
        }
        
        # Debug print statements for statistics
        print("\nDEBUG: Application Statistics:")
        for status, count in context['application_stats'].items():
            print(f"{status}: {count}")
        
        return context

class JobPostingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'jobs/job_posting_form.html'
    success_url = reverse_lazy('jobs:employer_dashboard')

    def test_func(self):
        return self.get_object().employer.user == self.request.user

class JobPostingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = JobPosting
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('jobs:job_list')

    def test_func(self):
        job = self.get_object()
        return job.employer.user == self.request.user

class JobToggleStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        job = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return job.employer.user == self.request.user

    def post(self, request, pk):
        job = get_object_or_404(JobPosting, pk=pk)
        job.is_active = not job.is_active
        job.save()
        messages.success(request, f'Job "{job.title}" has been {"activated" if job.is_active else "deactivated"}.')
        return redirect('jobs:job_detail', pk=job.pk)

def home(request):
    jobs = JobPosting.objects.filter(
        is_active=True,
        deadline__gte=timezone.now()
    ).order_by('-created_at')[:5]
    return render(request, 'home.html', {'jobs': jobs})

class SavedJobListView(LoginRequiredMixin, ListView):
    model = SavedJob
    template_name = 'jobs/saved_jobs.html'
    context_object_name = 'saved_jobs'

    def get_queryset(self):
        return SavedJob.objects.filter(
            job_seeker=self.request.user.jobseeker
        ).order_by('-saved_at')

class EmployerRegistrationView(CreateView):
    form_class = EmployerRegistrationForm
    template_name = 'jobs/employer_registration.html'
    success_url = reverse_lazy('jobs:employer_dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already logged in and has an employer profile, redirect to dashboard
        if request.user.is_authenticated and hasattr(request.user, 'employer'):
            messages.info(request, 'You are already registered as an employer.')
            return redirect('jobs:employer_dashboard')
            
        # If user is already a job seeker, show an error
        if request.user.is_authenticated and hasattr(request.user, 'jobseeker'):
            messages.error(request, 'You are already registered as a job seeker. Please use a different account to register as an employer.')
            return redirect('jobs:job_list')
            
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        
        # If user is not already logged in, log them in
        if not self.request.user.is_authenticated:
            # Set the backend and login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            
        messages.success(self.request, 'Employer account created successfully!')
        return response

class JobSeekerRegistrationView(CreateView):
    form_class = JobSeekerRegistrationForm
    template_name = 'jobs/jobseeker_registration.html'
    success_url = reverse_lazy('jobs:jobseeker_dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already logged in and has a job seeker profile, redirect to dashboard
        if request.user.is_authenticated and hasattr(request.user, 'jobseeker'):
            messages.info(request, 'You are already registered as a job seeker.')
            return redirect('jobs:jobseeker_dashboard')
            
        # If user is already an employer, show an error
        if request.user.is_authenticated and hasattr(request.user, 'employer'):
            messages.error(request, 'You are already registered as an employer. Please use a different account to register as a job seeker.')
            return redirect('jobs:job_list')
            
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        
        # If user is not already logged in, log them in
        if not self.request.user.is_authenticated:
            # Set the backend and login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            
        messages.success(self.request, 'Job seeker account created successfully!')
        return response

class HomeView(ListView):
    model = JobPosting
    template_name = 'jobs/home.html'
    context_object_name = 'jobs'
    
    def get_queryset(self):
        return JobPosting.objects.filter(
            is_active=True,
            deadline__gte=timezone.now()
        ).order_by('-created_at')[:6]

class JobSeekerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = JobSeeker
    form_class = JobSeekerProfileForm
    template_name = 'jobs/jobseeker_profile_form.html'
    success_url = reverse_lazy('jobs:jobseeker_dashboard')

    def get_object(self, queryset=None):
        return self.request.user.jobseeker

    def form_valid(self, form):
        # Print form data and current object state
        print("Form data:", form.cleaned_data)
        print("Current location:", self.get_object().location)
        
        # Save the form
        response = super().form_valid(form)
        
        # Print the new object state
        print("New location:", self.get_object().location)
        
        messages.success(self.request, 'Profile updated successfully!')
        return response

    def get_initial(self):
        # Get the current values
        initial = super().get_initial()
        jobseeker = self.get_object()
        print("Initial location:", jobseeker.location)
        return initial

class JobAlertListView(LoginRequiredMixin, ListView):
    model = JobAlert
    template_name = 'jobs/job_alert_list.html'
    context_object_name = 'alerts'

    def get_queryset(self):
        return JobAlert.objects.filter(job_seeker=self.request.user.jobseeker).order_by('-created_at')

class JobAlertCreateView(LoginRequiredMixin, CreateView):
    model = JobAlert
    form_class = JobAlertForm
    template_name = 'jobs/job_alert_form.html'
    success_url = reverse_lazy('jobs:job_alert_list')

    def form_valid(self, form):
        form.instance.job_seeker = self.request.user.jobseeker
        return super().form_valid(form)

class JobAlertUpdateView(LoginRequiredMixin, UpdateView):
    model = JobAlert
    form_class = JobAlertForm
    template_name = 'jobs/job_alert_form.html'
    success_url = reverse_lazy('jobs:job_alert_list')

    def get_queryset(self):
        return JobAlert.objects.filter(job_seeker=self.request.user.jobseeker)

class JobAlertDeleteView(LoginRequiredMixin, DeleteView):
    model = JobAlert
    template_name = 'jobs/job_alert_confirm_delete.html'
    success_url = reverse_lazy('jobs:job_alert_list')

    def get_queryset(self):
        return JobAlert.objects.filter(job_seeker=self.request.user.jobseeker)

class JobAlertToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        alert = get_object_or_404(JobAlert, pk=pk, job_seeker=request.user.jobseeker)
        alert.is_active = not alert.is_active
        alert.save()
        return redirect('jobs:job_alert_list')
