from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('EMPLOYEE', 'Employee'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    employee_number = models.CharField(max_length=10, unique=True, null=True, blank=True)  # Added this line

class Punch(models.Model):
    PUNCH_TYPES = (
        ('IN', 'Punch In'),
        ('OUT', 'Punch Out'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='punches')
    punch_type = models.CharField(max_length=3, choices=PUNCH_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.punch_type} - {self.timestamp}"

class TimeclockBox(models.Model):
    box_id = models.CharField(max_length=100, unique=True)  # Unique ID or Serial Number for the box
    location = models.CharField(max_length=255)  # Description or location of the box
    last_connected = models.DateTimeField(null=True, blank=True)  # Timestamp of the last successful connection

class DailyHours(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    total_hours = models.DurationField()

class WeeklyHours(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    week_start_date = models.DateField()
    total_hours = models.DurationField()
