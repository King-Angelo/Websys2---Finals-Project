# Generated by Django 5.1.7 on 2025-04-02 15:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_jobposting_applications_count_jobposting_benefits_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobalert',
            name='jobseeker',
        ),
        migrations.AlterUniqueTogether(
            name='jobmatch',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='jobmatch',
            name='job',
        ),
        migrations.RemoveField(
            model_name='jobmatch',
            name='jobseeker',
        ),
        migrations.RemoveField(
            model_name='message',
            name='receiver',
        ),
        migrations.RemoveField(
            model_name='message',
            name='sender',
        ),
        migrations.RemoveField(
            model_name='profileview',
            name='profile',
        ),
        migrations.RemoveField(
            model_name='profileview',
            name='viewer',
        ),
        migrations.RemoveField(
            model_name='jobposting',
            name='applications_count',
        ),
        migrations.RemoveField(
            model_name='jobposting',
            name='benefits',
        ),
        migrations.RemoveField(
            model_name='jobposting',
            name='experience_level',
        ),
        migrations.RemoveField(
            model_name='jobposting',
            name='job_category',
        ),
        migrations.RemoveField(
            model_name='jobposting',
            name='preferred_skills',
        ),
        migrations.RemoveField(
            model_name='jobposting',
            name='remote_option',
        ),
        migrations.RemoveField(
            model_name='jobposting',
            name='required_skills',
        ),
        migrations.RemoveField(
            model_name='jobposting',
            name='views_count',
        ),
        migrations.RemoveField(
            model_name='jobseeker',
            name='availability',
        ),
        migrations.RemoveField(
            model_name='jobseeker',
            name='certifications',
        ),
        migrations.RemoveField(
            model_name='jobseeker',
            name='expected_salary',
        ),
        migrations.RemoveField(
            model_name='jobseeker',
            name='portfolio_links',
        ),
        migrations.RemoveField(
            model_name='jobseeker',
            name='preferred_job_types',
        ),
        migrations.RemoveField(
            model_name='jobseeker',
            name='preferred_locations',
        ),
        migrations.RemoveField(
            model_name='jobseeker',
            name='professional_summary',
        ),
        migrations.CreateModel(
            name='SavedJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobs.jobposting')),
                ('job_seeker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobs.jobseeker')),
            ],
            options={
                'unique_together': {('job_seeker', 'job')},
            },
        ),
        migrations.DeleteModel(
            name='Interview',
        ),
        migrations.DeleteModel(
            name='JobAlert',
        ),
        migrations.DeleteModel(
            name='JobMatch',
        ),
        migrations.DeleteModel(
            name='Message',
        ),
        migrations.DeleteModel(
            name='ProfileView',
        ),
    ]
