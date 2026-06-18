# appointments/models.py
from django.db import models
from django.conf import settings

from accounts.models import DoctorProfile, PatientProfile


class DoctorSlot(models.Model):
    """
    Time slots created by doctors to show their availability.
    """
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.start_time} - {self.end_time})"


class Appointment(models.Model):
    """
    Handles the lifecycle of a patient's appointment request.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Patient Request'),
        ('DOCTOR_CONFIRMED', 'Slot Confirmed by Doctor'),
        ('APPROVED', 'Approved by Admin'),
        ('REJECTED', 'Rejected/Cancelled'),
    ]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    slot = models.ForeignKey(DoctorSlot, on_delete=models.SET_NULL, null=True, blank=True)
    
    preferred_date = models.DateField(help_text="The date patient wants to see the doctor")
    preferred_time_notes = models.CharField(max_length=255, blank=True, help_text="e.g., Evening after 6 PM")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    symptoms = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment #{self.id} - {self.patient} with {self.doctor} ({self.status})"