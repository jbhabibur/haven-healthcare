import json
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import (
    LoginView, 
    LogoutView, 
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib import messages

# Imports required for decoding email activation tokens
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator

from .forms import CustomUserCreationForm
from .models import PatientProfile, DoctorProfile

User = get_user_model()


# --- Authentication & Registration ---

class SignUpView(CreateView):
    """
    Handles user user registration using the custom user creation form.
    """
    form_class = CustomUserCreationForm
    template_name = 'accounts/registration/signup.html'
    success_url = reverse_lazy('accounts:login') 

    def form_valid(self, form):
        # Saved instance triggers post_save signals for profile creation
        user = form.save(commit=False)
        user.is_active = False  
        user.save()
        return super().form_valid(form)


class MyLoginView(LoginView):
    """
    Handles user login authentication and ensures unverified users are blocked.
    """
    template_name = 'accounts/registration/login.html'

    def form_invalid(self, form):
        username = form.cleaned_data.get('username')
        if username:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    messages.error(self.request, "Your account is not activated yet. Please check your email for the verification link.")
            except User.DoesNotExist:
                pass
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('home')


class MyLogoutView(LogoutView):
    """
    Handles user logout session destruction.
    """
    next_page = reverse_lazy('accounts:login')


# --- Email Verification Activation ---

def activate_account(request, uidb64, token):
    """
    Decodes the user ID from base64 and validates the unique email token.
    If valid, activates the user account so they can log in.
    """
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

class MyPasswordResetView(PasswordResetView):
    """
    Initiates the password reset process by accepting an email.
    """
    template_name = 'accounts/registration/password_reset_form.html'
    email_template_name = 'accounts/registration/password_reset_email.html'
    html_email_template_name = 'accounts/registration/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class MyPasswordResetDoneView(PasswordResetDoneView):
    """
    Displays a success message indicating that a reset email has been sent.
    """
    template_name = 'accounts/registration/password_reset_done.html'


class MyPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Validates the unique link sent via email and allows entering a new password.
    """
    template_name = 'accounts/registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class MyPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Displays confirmation that the password has been successfully updated.
    """
    template_name = 'accounts/registration/password_reset_complete.html'


# --- AJAX Profile Phone Update ---

@login_required
@require_POST
def update_phone_ajax(request):
    """
    AJAX view to instantly update the logged-in patient's phone number 
    from the appointment page.
    """
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


# --- Profile Management ---

@login_required
def profile_redirect_view(request):
    """
    Checks the user's role and redirects them to the appropriate profile URL.
    """
    # Check if the logged-in user is a doctor
    if getattr(request.user, 'is_doctor', False):
        return redirect('accounts:doctor_profile')
        
    # Check if the logged-in user is a patient
    elif getattr(request.user, 'is_patient', False):
        return redirect('accounts:patient_profile')
    
    # Fallback to home page if no specific role matches (e.g., admin)
    return redirect('home')


@login_required
def doctor_profile_view(request):
    """
    Renders the doctor dashboard displaying profile details, 
    allowing updates, and showing patient records.
    """
    # 1. Fetch the logged-in user's doctor profile, or create one if it doesn't exist
    doctor_profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    # 2. Handle profile updates when the form is submitted via POST
    if request.method == 'POST':
        doctor_profile.specialization = request.POST.get('specialization', '').strip()
        doctor_profile.registration_number = request.POST.get('registration_number', '').strip()
        
        # Handle validation for numeric fields
        try:
            doctor_profile.consultation_fee = request.POST.get('consultation_fee') or 0.00
            doctor_profile.follow_up_fee = request.POST.get('follow_up_fee') or 0.00
            doctor_profile.follow_up_validity_days = request.POST.get('follow_up_validity_days') or 14
        except (ValueError, TypeError):
            pass
            
        doctor_profile.qualification = request.POST.get('qualification', '').strip()
        doctor_profile.doctor_info = request.POST.get('doctor_info', '').strip()
        
        # Set boolean value for the availability checkbox
        doctor_profile.is_available = 'is_available' in request.POST
        
        # Handle image uploads (compatible with Cloudinary)
        if 'image' in request.FILES:
            doctor_profile.image = request.FILES['image']
            
        # Save updated data to the database
        doctor_profile.save()
        messages.success(request, "Your profile has been updated successfully!")
        return redirect('accounts:doctor_profile')

    # 3. Fetch patient records using an optimized query
    patients = PatientProfile.objects.select_related('user').all().order_by('-created_at')
    
    context = {
        'doctor_profile': doctor_profile,
        'patients': patients,
    }
    return render(request, 'accounts/doctor_profile.html', context)


@login_required
def patient_profile_view(request):
    """
    Renders the dashboard customized for the patient by fetching data from the database.
    """
    # Dynamic database instance target setup
    patient_profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    context = {
        'patient_profile': patient_profile,
    }
    return render(request, 'accounts/patient_profile.html', context)