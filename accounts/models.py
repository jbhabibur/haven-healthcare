from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.apps import AppConfig

# --- Custom User Model ---
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MODERATOR = "MODERATOR", "Moderator"
        PATIENT = "PATIENT", "Patient"
        DOCTOR = "DOCTOR", "Doctor"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)

    # Helper methods to check roles easily
    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT


# --- Doctor Profile ---
class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100, blank=True)
    qualification = models.TextField(blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"


# --- Patient Profile ---
class PatientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    medical_history = models.TextField(blank=True)

    def __str__(self):
        return f"Patient: {self.user.username}"
    

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals  # এখানে সিগন্যাল লোড হবে