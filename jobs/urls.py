from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/create/', views.JobPostingCreateView.as_view(), name='job_create'),
    path('jobs/<int:pk>/update/', views.JobPostingUpdateView.as_view(), name='job_update'),
    path('jobs/<int:pk>/delete/', views.JobPostingDeleteView.as_view(), name='job_delete'),
    path('jobs/<int:pk>/toggle-status/', views.JobToggleStatusView.as_view(), name='job_toggle_status'),
    path('jobs/<int:job_id>/apply/', views.ApplicationCreateView.as_view(), name='job_apply'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='application_edit'),
    path('applications/<int:pk>/update/', views.ApplicationUpdateView.as_view(), name='application_update'),
    path('applications/<int:pk>/status/', views.ApplicationStatusUpdateView.as_view(), name='application_status_update'),
    path('employer/dashboard/', views.EmployerDashboardView.as_view(), name='employer_dashboard'),
    path('jobseeker/dashboard/', views.JobSeekerDashboardView.as_view(), name='jobseeker_dashboard'),
    path('employer/registration/', views.EmployerRegistrationView.as_view(), name='employer_registration'),
    path('jobseeker/registration/', views.JobSeekerRegistrationView.as_view(), name='jobseeker_registration'),
    path('jobs/<int:job_id>/save/', views.SavedJobView.as_view(), name='save_job'),
    path('saved-jobs/', views.SavedJobListView.as_view(), name='saved_jobs'),
    path('jobseeker/profile/edit/', views.JobSeekerProfileUpdateView.as_view(), name='jobseeker_profile_edit'),
    path('alerts/', views.JobAlertListView.as_view(), name='job_alert_list'),
    path('alerts/create/', views.JobAlertCreateView.as_view(), name='job_alert_create'),
    path('alerts/<int:pk>/update/', views.JobAlertUpdateView.as_view(), name='job_alert_update'),
    path('alerts/<int:pk>/delete/', views.JobAlertDeleteView.as_view(), name='job_alert_delete'),
    path('alerts/<int:pk>/toggle/', views.JobAlertToggleView.as_view(), name='job_alert_toggle'),
]
