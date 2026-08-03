# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms import Textarea
from django.db import models as django_models

from .models import User, DoctorProfile, DoctorExperience, DoctorReview, PatientProfile, MedicalRecord

# Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    
    # REQUIRED for autocomplete_fields to work on other models
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    # Safe list unpacking for fieldsets inheritance
    fieldsets = UserAdmin.fieldsets + (
        ('Role Management', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Management', {'fields': ('role',)}),
    )


# Inline Configurations for Doctor Profile
class DoctorExperienceInline(admin.TabularInline):
    model = DoctorExperience
    fields = ('institution_name', 'designation', 'department', 'start_date', 'end_date')
    extra = 1  # Number of empty slots shown by default for new entries

# Inline Configuration for Doctor Reviews
class DoctorReviewInline(admin.TabularInline):
    model = DoctorReview
    extra = 0
    # Set fields to read-only so administrators cannot alter submitted patient feedback
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    
    # Disables adding new reviews manually from the doctor interface layout
    def has_add_permission(self, request, obj=None):
        return False


# Doctor Profile Admin
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('get_doctor_name', 'image', 'specialization', 'registration_number', 'consultation_fee', 'follow_up_fee', 'is_available')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'registration_number', 'specialization')
    list_filter = ('is_available', 'specialization')

    formfield_overrides = {
        django_models.TextField: {'widget': Textarea(attrs={'rows': 15, 'cols': 85})},
    }
    
    autocomplete_fields = ('user',)
    
    fieldsets = (
        ('User Link', {'fields': ('user',)}),
        ('Professional Info', {'fields': ('image', 'specialization', 'qualification', 'registration_number', 'is_available')}),
        ('Fees & Validity', {
            'fields': (
                'consultation_fee', 
                ('follow_up_fee', 'follow_up_validity_days')
            )
        }),
        ('Descriptions & Bio', {'fields': ('specialty_description', 'doctor_info')}),
    )
    
    # Inlines list layout loaded below the doctor core profile info
    inlines = [DoctorExperienceInline, DoctorReviewInline]

    @admin.display(description='Doctor Name', ordering='user__first_name')
    def get_doctor_name(self, obj):
        """Displays clear target naming representation on dashboard rows with proper column sorting"""
        return str(obj)


# Doctor Review Admin (Standalone View)
@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name', 'user__username', 'comment')
    readonly_fields = ('created_at',)
    
    autocomplete_fields = ('doctor', 'user')

    
# Medical Record Admin
@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'diagnosis', 'date_recorded')
    list_filter = ('date_recorded', 'doctor')
    search_fields = ('patient__user__first_name', 'diagnosis', 'doctor__user__first_name')
    autocomplete_fields = ('patient', 'doctor')
    
    readonly_fields = ('date_recorded', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser and not request.user.is_doctor:
            return [field.name for field in self.model._meta.fields]
        return self.readonly_fields
    

# Medical Record Inline Configuration
class MedicalRecordInline(admin.TabularInline):
    model = MedicalRecord
    extra = 0
    fields = ('doctor', 'diagnosis', 'treatment_notes', 'date_recorded')
    readonly_fields = ('date_recorded',)

    # This ensures that only superusers and doctors can add or change medical records inline, while others can only view them.
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_doctor

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_doctor


# Patient Profile Admin
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('get_patient_name', 'phone_number', 'age', 'blood_group')
    search_fields = ('user__username', 'user__first_name', 'last_name', 'user__email', 'phone_number', 'blood_group')
    list_filter = ('blood_group',)
    
    autocomplete_fields = ('user',)

    # Include the inline configuration here
    inlines = [MedicalRecordInline] 

    @admin.display(description='Patient Name', ordering='user__username')
    def get_patient_name(self, obj):
        return str(obj)