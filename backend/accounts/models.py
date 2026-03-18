from django.contrib.auth.models import User
from django.db import models
from simple_history.models import HistoricalRecords


class UserProfile(models.Model):
    ROLE_FOREMAN = 'foreman'
    ROLE_PM = 'pm'
    ROLE_OFFICE = 'office'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_FOREMAN, 'Foreman / Superintendent'),
        (ROLE_PM, 'Project Manager'),
        (ROLE_OFFICE, 'Office / Accounting'),
        (ROLE_ADMIN, 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'
