from django.contrib.auth.models import AbstractUser
from django.db import models

from comp3820 import settings


# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [
        ("midwife", "Midwife"),
        ("admin", "Administrator"),
    ]

    staff_id = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name()} {self.staff_id}"

    class Handover(models.Model):
        encounter_id = models.CharField(max_length=64)
        patient_id = models.CharField(max_length=64)
        from_staff = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            related_name="handover_from"
        )
        to_staff = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            related_name="handover_to"
        )
        notes = models.TextField()
        urgent_alerts = models.TextField(blank=True, null=True)
        created_at = models.DateTimeField(auto_now_add=True)

class MotherChild(models.Model):
    mother_id = models.CharField(max_length=50)
    child_id = models.CharField(max_length=50)
    bed_id = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Mother:  ({self.mother_id}) - Child:  ({self.child_id})"

class ShiftSchedule(models.Model):
    SHIFT_CHOICES = [
        ('night', '00:00 - 08:00'),
        ('day', '08:00 - 16:00'),
        ('evening', '16:00 - 24:00'),
    ]

    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES)

    class Meta:
        unique_together = ('staff', 'date', 'shift')
        ordering = ['date', 'shift']

    def __str__(self):
        return f"{self.staff.get_full_name()} ({self.staff.staff_id}) - {self.get_shift_display()} on {self.date}"
