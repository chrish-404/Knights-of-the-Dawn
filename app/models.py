from django.contrib.auth.models import AbstractUser
from django.db import models

from comp3820 import settings


# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [
        ("midwife", "Midwife"),
        ("nurse", "Nurse"),
        ("doctor", "Doctor"),
        ("admin", "Administrator"),
    ]

    staff_id = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role}){self.staff_id}"

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
