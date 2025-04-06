import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from jobs.models import JobSeeker

def create_jobseeker_profile():
    # Get the first user (or you can specify a username)
    user = User.objects.first()
    
    if not user:
        print("No users found in the database!")
        return
    
    # Check if user already has a JobSeeker profile
    if hasattr(user, 'jobseeker'):
        print(f"User {user.username} already has a JobSeeker profile!")
        return
    
    # Create JobSeeker profile
    JobSeeker.objects.create(
        user=user,
        phone='',  # Can be updated later
        address='',  # Can be updated later
        education='',  # Can be updated later
        experience='',  # Can be updated later
        skills=''  # Can be updated later
    )
    
    print(f"Successfully created JobSeeker profile for user: {user.username}")

if __name__ == '__main__':
    create_jobseeker_profile() 