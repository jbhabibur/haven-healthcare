from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db.models import Avg
from datetime import date
from dateutil.relativedelta import relativedelta
from cloudinary.models import CloudinaryField
from django.db.models.signals import post_save
from django.dispatch import receiver


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

    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username


# --- Doctor Profile ---
class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_profile'
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
            "এডমিন নির্দেশিকা: ডক্টরের মূল পরিচিতি, চিকিৎসাপ্রাপ্ত রোগের তালিকা এবং নিচের "
            "স্লোগানটি ইমেজের বা প্রেসক্রিপশনের মতো হুবহু এন্টার (New Line) দিয়ে দিয়ে এখানে পেস্ট করুন। "
            "কোনോ প্রকার HTML ট্যাগ ব্যবহারের প্রয়োজন নেই, ফ্রন্টএন্ডে এটি স্বয়ংক্রিয়ভাবে সাজিয়ে নিবে।"
        )
    )
    
    # Fees
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    follow_up_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Fee for follow-up visits")
    follow_up_validity_days = models.PositiveIntegerField(default=14, help_text="Number of days the follow-up fee is applicable")

    is_available = models.BooleanField(default=True)
    
    # --- Admin Approval Fields for Doctors ---
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


# --- Doctor Experience ---
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
        """
        Helper property to automatically format experience duration as 'X years Y months Z days'
        """
        end = self.end_date if self.end_date else date.today()
        delta = relativedelta(end, self.start_date)
        
        parts = []
        if delta.years > 0:
            parts.append(f"{delta.years} years")
        if delta.months > 0:
            parts.append(f"{delta.months} months")
        if delta.days > 0:
            parts.append(f"{delta.days} days")
            
        return ", ".join(parts) if parts else "0 days"


# --- Doctor Review & Rating System ---
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


# --- Patient Profile ---
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
    medical_history = models.TextField(blank=True)
    
    # --- Admin Approval Fields for Patients ---
    is_approved = models.BooleanField(default=False, help_text="Designates whether this patient is approved by admin.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user.first_name or self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.user.username