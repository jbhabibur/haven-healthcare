# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db.models import Avg
from datetime import date
from dateutil.relativedelta import relativedelta
from cloudinary.models import CloudinaryField


# Custom User Model
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

    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username


# Doctor Profile Model  
class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_profile',
        unique=True
    )

    image = CloudinaryField(
        'image', 
        folder='doctors',
        blank=True, 
        null=True,
        help_text="Upload doctor's profile picture to Cloudinary (Optional)"
    )

    specialization = models.CharField(max_length=100, blank=True)
    qualification = models.TextField(blank=True, help_text="E.g., BUMS (Rajshahi Medical University) M.Sc...")
    specialty_description = models.TextField(blank=True, help_text="For displaying specialized medical services text")
    registration_number = models.CharField(max_length=50, blank=True, null=True, help_text="E.g., U-543")

    doctor_info = models.TextField(
        blank=True, 
        null=True, 
        help_text=(
            "Admin Guideline: Paste the doctor's main introduction, treated disease list, and slogan "
            "exactly as it appears on their prescription or image using the Enter key (New Line). "
            "No HTML tags are required; the frontend will format it automatically."
        )
    )
    
    # Fees
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    follow_up_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Fee for follow-up visits")
    follow_up_validity_days = models.PositiveIntegerField(default=14, help_text="Number of days the follow-up fee is applicable")

    is_available = models.BooleanField(default=True)
    
    # Admin Approval Fields for Doctors
    is_approved = models.BooleanField(default=False, help_text="Designates whether this doctor is approved by admin.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user.first_name or self.user.last_name:
            return f"Dr. {self.user.first_name} {self.user.last_name}".strip()
        return f"Dr. {self.user.username}"

    @property
    def total_experience_years(self):
        """
        Loops through all associated experiences and calculates cumulative years (E.g., '2+ Years')
        """
        total_days = 0
        for exp in self.experiences.all():
            end = exp.end_date if exp.end_date else date.today()
            total_days += (end - exp.start_date).days
        
        years = total_days // 365
        return f"{years}+ Years" if years > 0 else "Fresh"

    @property
    def average_rating(self):
        """
        Dynamically calculates and averages all profile reviews (E.g., 4.80)
        """
        result = self.reviews.aggregate(avg_rating=Avg('rating'))
        return round(result['avg_rating'], 2) if result['avg_rating'] else 0.00

    @property
    def total_reviews_count(self):
        """Returns total reviews count (E.g., 10)"""
        return self.reviews.count()


# Doctor Experience Model
class DoctorExperience(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='experiences')
    institution_name = models.CharField(max_length=255) 
    designation = models.CharField(max_length=100)      
    department = models.CharField(max_length=100, blank=True, null=True) 
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank if currently working here")
    
    class Meta:
        ordering = ['-start_date']  # Displays latest experience on top

    def __str__(self):
        return f"{self.designation} at {self.institution_name}"

    @property
    def duration_text(self):
        # start_date and end_date are required to calculate duration; if not present, return "N/A"
        if not self.start_date:
            return "N/A"
            
        end = self.end_date if self.end_date else date.today()

        # Calculate the difference in years, months, and days using relativedelta
        try:
            delta = relativedelta(end, self.start_date)
        except TypeError:
            return "N/A"
            
        parts = []
        if delta.years > 0:
            parts.append(f"{delta.years} {'year' if delta.years == 1 else 'years'}")
        if delta.months > 0:
            parts.append(f"{delta.months} {'month' if delta.months == 1 else 'months'}")
        if delta.days > 0:
            parts.append(f"{delta.days} {'day' if delta.days == 1 else 'days'}")
                
        return ", ".join(parts) if parts else "0 days"


# Doctor Review & Rating System Model
class DoctorReview(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_reviews') 
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        ordering = ['-created_at'] 
        unique_together = ('doctor', 'user') 

    def __str__(self):
        return f"Review ({self.rating}★) for {self.doctor} by {self.user}"


# Patient Profile Model
class PatientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')

    phone_regex = RegexValidator(
        regex=r'^\+?(88)?01[3-9]\d{8}$', 
        message="Phone number must be entered in the format: '01XXXXXXXXX' or '+8801XXXXXXXXX'. Up to 14 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=15, 
        blank=True, 
        null=True, 
        unique=True,
        help_text="Enter patient's valid phone number"
    )

    age = models.PositiveIntegerField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)

    address = models.TextField(blank=True, null=True, help_text="Enter patient's full address")

    image = CloudinaryField(
        'image', 
        folder='patients',
        blank=True, 
        null=True,
        help_text="Upload patient's profile picture to Cloudinary (Optional)"
    )
    
    # Admin Approval Fields for Patients
    is_approved = models.BooleanField(default=False, help_text="Designates whether this patient is approved by admin.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user.first_name or self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.user.username


# Medical Record Model 
class MedicalRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey('accounts.DoctorProfile', on_delete=models.SET_NULL, null=True, related_name='recorded_histories')
    
    diagnosis = models.CharField(max_length=255)
    symptoms = models.TextField(blank=True, null=True)
    treatment_notes = models.TextField()
    prescribed_medication = models.JSONField(blank=True, null=True, help_text="JSON format: {'meds': ['Napa', 'Seclo']}")
    
    date_recorded = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_recorded']

    def __str__(self):
        return f"{self.patient.user.first_name} - {self.diagnosis}"