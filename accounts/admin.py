from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.forms import Textarea
from django.db import models as django_models
from .models import User, DoctorProfile, DoctorExperience, DoctorReview, PatientProfile


# --- Custom User Admin ---
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Extends standard UserAdmin to display and manage custom user roles"""
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


# --- Inline Configurations for Doctor Profile ---
class DoctorExperienceInline(admin.TabularInline):
    """Enables managing multiple experiences directly inside the Doctor Profile detail view"""
    model = DoctorExperience
    fields = ('institution_name', 'designation', 'department', 'start_date', 'end_date')
    extra = 1  # Number of empty slots shown by default for new entries


class DoctorReviewInline(admin.TabularInline):
    """Enables viewing patients' feedback directly inside the Doctor Profile detail view"""
    model = DoctorReview
    extra = 0
    # Set fields to read-only so administrators cannot alter submitted patient feedback
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    
    # Disables adding new reviews manually from the doctor interface layout
    def has_add_permission(self, request, obj=None):
        return False


# --- Doctor Profile Admin ---
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


# --- Doctor Review Admin (Standalone View) ---
@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    """Standalone module to manage and audit patient reviews globally"""
    list_display = ('doctor', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name', 'user__username', 'comment')
    readonly_fields = ('created_at',)
    
    autocomplete_fields = ('doctor', 'user')


# --- Patient Profile Admin ---
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    """Manages simple list view records for registered patients"""
    list_display = ('get_patient_name', 'age', 'blood_group')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'blood_group')
    list_filter = ('blood_group',)
    
    autocomplete_fields = ('user',)

    @admin.display(description='Patient Name', ordering='user__username')
    def get_patient_name(self, obj):
        return str(obj)