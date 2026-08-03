# accounts/views.py

import json

# Django Core & Shortcuts
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError

# Django Views & CBVs
from django.views.generic import CreateView
from django.views.decorators.http import require_POST
from django.contrib.auth.views import (
    LoginView, 
    LogoutView, 
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)

# Django Decorators & Messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

# Django Auth & Tokens
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator


# Third-party Apps (Cloudinary)
import cloudinary.uploader

# Local Models
from .models import (
    PatientProfile, 
    DoctorProfile, 
    MedicalRecord, 
    DoctorExperience
)
from appointments.models import DoctorSlot, Appointment

# Local Forms
from .forms import (
    LoginForm, 
    MyPasswordResetForm, 
    MySetPasswordForm,
    CustomUserCreationForm,
)

# Global Variables
User = get_user_model()




# --- Authentication & Registration ---
# User registration endpoint
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/registration/signup.html'
    success_url = reverse_lazy('accounts:login') 

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  
        user.save()
        # Success message for registration
        messages.success(self.request, "Registration successful! Please check your email to activate your account.")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Error message if the registration form fails validation
        messages.error(self.request, "Registration failed. Please verify the provided details.")
        return super().form_invalid(form)

# User login endpoint
class MyLoginView(LoginView):
    template_name = 'accounts/registration/login.html'
    form_class = LoginForm 

    def form_invalid(self, form):
        username = form.cleaned_data.get('username')
        
        if username:
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    # Message for unverified users
                    messages.error(self.request, "Your account is not activated yet. Please check your email for the verification link.")
                else:
                    # Message for correct username but incorrect password
                    messages.error(self.request, "Invalid username or password.")
            except User.DoesNotExist:
                # Message if the username does not exist
                messages.error(self.request, "No account found with this username.")
        else:
            # Message if form fields are empty or invalid
            messages.error(self.request, "Please enter both your username and password.")
            
        return super().form_invalid(form)

    def get_success_url(self):
        # Optional success message upon successful login
        messages.success(self.request, "Welcome back! You have successfully logged in.")
        return reverse_lazy('home')

# User logout endpoint
class MyLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        # Clear any existing messages to avoid duplicates
        storage = messages.get_messages(request)
        storage.used = True 
        
        # Add a success message for logout
        messages.success(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)




# --- Email Verification Activation ---
def activate_account(request, uidb64, token):
    try:
        # Decode user primary key from base64 string
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Verify if the user exists and the token matches/has not expired
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        
        # Render success message layout
        return render(request, 'accounts/registration/activation_success.html', {'user': user})
    else:
        # Render fallback structure if the verification link is faulty or expired
        return render(request, 'accounts/registration/activation_invalid.html')



# --- Password Reset Flow ---
# Request password reset email
class MyPasswordResetView(PasswordResetView):
    """
    Initiates the password reset process by accepting an email.
    """
    template_name = 'accounts/registration/password_reset_form.html'
    form_class = MyPasswordResetForm
    email_template_name = 'accounts/registration/password_reset_email.html'
    html_email_template_name = 'accounts/registration/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')

 # Password reset email sent notification
class MyPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/registration/password_reset_done.html'

# Enter new password form
class MyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = MySetPasswordForm

# Password reset success confirmation
class MyPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/registration/password_reset_complete.html'




# --- Profile Management ---
# Central profile routing based on user role (doctor/patient)
@login_required
def profile_redirect_view(request):
    # Check if the logged-in user is a doctor
    if getattr(request.user, 'is_doctor', False):
        return redirect('accounts:doctor_profile')
        
    # Check if the logged-in user is a patient
    elif getattr(request.user, 'is_patient', False):
        return redirect('accounts:patient_profile')
    
    # Fallback to home page if no specific role matches (e.g., admin)
    return redirect('home')

# Patient dashboard profile view
@login_required
def patient_profile_view(request):
    # Query the logged-in user's patient profile or create one if it doesn't exist
    patient_profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    # Medical records query (with select_related for doctor user) and pagination
    records_list = MedicalRecord.objects.filter(patient=patient_profile).select_related(
        'doctor__user'
    ).order_by('-date_recorded')
    
    history_paginator = Paginator(records_list, 5)
    history_page = request.GET.get('history_page')
    medical_records = history_paginator.get_page(history_page)
    
    # Appointments query and pagination
    appointments_list = Appointment.objects.filter(patient=patient_profile).order_by('-created_at')
    
    appointment_paginator = Paginator(appointments_list, 5)
    page_number = request.GET.get('page')
    appointments = appointment_paginator.get_page(page_number)
    
    
    context = {
        'patient_profile': patient_profile,
        'medical_records': medical_records, 
        'appointments': appointments,
    }
    
    return render(request, 'accounts/patient_profile.html', context)

# Doctor dashboard profile view
@login_required
def doctor_profile_view(request):
    doctor = get_object_or_404(DoctorProfile.objects.select_related('user'), user=request.user)
    doctor_slots = DoctorSlot.objects.filter(doctor__user=request.user).order_by('date', 'start_time')
    patients = PatientProfile.objects.all().order_by('-created_at')

    exp_queryset = DoctorExperience.objects.filter(doctor=doctor)
    
    experiences = []
    for exp in exp_queryset:
        experiences.append({
            'id': exp.id,
            'institution_name': exp.institution_name,
            'designation': exp.designation,
            'duration': exp.duration_text,
            'start_date': str(exp.start_date),
            'end_date': str(exp.end_date) if exp.end_date else ""
        })

    print("expre", experiences)

    context = {
        "doctor": doctor,
        'patients': patients,
        'slots': doctor_slots,
        'experiences': experiences,
    }
    
    return render(request, 'accounts/doctor_profile.html', context)

# Patient profile update form view
@login_required
def update_patient_profile(request):
    patient_profile = get_object_or_404(PatientProfile, user=request.user)

    if request.method == 'POST':
        # Image removal logic
        if request.POST.get('remove_image') == 'true' and patient_profile.image:
            cloudinary.uploader.destroy(patient_profile.image.public_id)
            patient_profile.image = None
        
        # Add logic for new image upload
        if request.FILES.get('image'):
            if patient_profile.image:
                cloudinary.uploader.destroy(patient_profile.image.public_id)
            patient_profile.image = request.FILES['image']
            
        # Others information update for patient
        patient_profile.blood_group = request.POST.get('blood_group')
        patient_profile.age = request.POST.get('age')
        patient_profile.phone_number = request.POST.get('phone_number')
        patient_profile.address = request.POST.get('address')
        
        patient_profile.save()
        return redirect('accounts:patient_profile')

    return render(request, 'profile_edit.html', {'patient_profile': patient_profile})

# Doctor profile update form view
@login_required
def update_doctor_profile(request):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=405)

    data = json.loads(request.body)

    user = request.user
    doctor = request.user.doctor_profile

    user_fields = {f.name for f in user._meta.fields}
    doctor_fields = {f.name for f in doctor._meta.fields}

    for field, value in data.items():

        if field in user_fields:
            setattr(user, field, value)

        elif field in doctor_fields:
            setattr(doctor, field, value)

    user.save()
    doctor.save()

    return JsonResponse({
        "status": "success"
    })

# Update doctor profile picture
@login_required
@require_POST
def update_doctor_image(request):
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    
    # Remove logic for doctor profile image
    if request.POST.get('remove_image') == 'true':
        if doctor_profile.image:
            cloudinary.uploader.destroy(doctor_profile.image.public_id)
            doctor_profile.image = None
            doctor_profile.save()
        return JsonResponse({'status': 'success', 'image_url': None})
    
    # Add logic for new image upload
    if request.FILES.get('image'):
        if doctor_profile.image:
            cloudinary.uploader.destroy(doctor_profile.image.public_id)
        
        doctor_profile.image = request.FILES['image']
        doctor_profile.save()
        
        return JsonResponse({'status': 'success', 'image_url': doctor_profile.image.url})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)




# --- AJAX Profile Phone Update  ---
@login_required
@require_POST
def update_phone_ajax(request):
    try:
        data = json.loads(request.body)
        new_phone = data.get('phone_number', '').strip()
        
        if not new_phone:
            return JsonResponse({'success': False, 'error': 'Phone number cannot be empty.'}, status=400)
            
        # Get patient profile or create one if it doesn't exist
        profile, created = PatientProfile.objects.get_or_create(user=request.user)
        
        # Set new phone number and run model validation (for Regex & Unique constraints)
        profile.phone_number = new_phone
        profile.full_clean() 
        profile.save()
        
        return JsonResponse({'success': True, 'phone_number': profile.phone_number})
        
    except ValidationError as e:
        # Return validation errors (e.g., from RegexValidator or unique constraints) to the frontend
        error_msg = e.message_dict.get('phone_number', ['Invalid data provided.'])[0]
        return JsonResponse({'success': False, 'error': error_msg}, status=400)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An internal server error occurred. Please try again.'}, status=500)




# --- Appointment Actions ---
# Approve patient appointment request
@login_required
def approve_patient_view(request, pk):
    if request.method == "POST":
        patient = get_object_or_404(PatientProfile, pk=pk)
        patient.is_approved = True
        patient.save()
    return redirect('accounts:doctor_profile')

# Cancel patient appointment request
@login_required
def cancel_patient_view(request, pk):
    if request.method == "POST":
        appointment = get_object_or_404(Appointment, pk=pk)
        
        # Cancel or Delete Logic
        if appointment.patient.user == request.user:
            appointment.status = 'CANCELLED'
            appointment.save()
        elif request.user.is_staff or getattr(request.user, 'is_doctor', False) or getattr(request.user, 'is_moderator', False):
            appointment.delete()

        appointments_list = Appointment.objects.filter(patient__user=appointment.patient.user).order_by('-id')
        
        paginator = Paginator(appointments_list, 5) 
        page_number = request.GET.get('page', 1)
        appointments = paginator.get_page(page_number)
        
        return render(request, 'accounts/includes/_patient_appointment_content.html', {
            'appointments': appointments
        })




# --- Doctor Experience Management ---
# Add professional experience for doctor
@login_required
def add_experience(request):
    if request.method == 'POST':
        
        data = json.loads(request.body)
        print("Received Data:", data)
        doctor = request.user.doctor_profile
        exp = DoctorExperience.objects.create(
            doctor=doctor,
            institution_name=data.get('institution_name'),
            designation=data.get('designation'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date') or None
        )
        return JsonResponse({
            "status": "success",
            "experience": {
                "id": exp.id,
                "institution_name": exp.institution_name,
                "designation": exp.designation,
                "duration": exp.duration_text,
                "start_date": str(exp.start_date),
                "end_date": str(exp.end_date) if exp.end_date else ""
            }
        })
    return JsonResponse({"status": "error"}, status=400)

# Delete professional experience by ID  
@login_required
def delete_experience(request, pk):
    experience = get_object_or_404(DoctorExperience, pk=pk, doctor__user=request.user)
    experience.delete()
    return JsonResponse({"status": "success"})