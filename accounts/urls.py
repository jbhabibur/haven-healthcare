# accounts/urls.py

from django.urls import path
from .views import (
    SignUpView, 
    MyLoginView, 
    MyLogoutView, 
    MyPasswordResetView,
    MyPasswordResetDoneView,
    MyPasswordResetConfirmView,
    MyPasswordResetCompleteView,
    activate_account,
    approve_patient_view,
    cancel_patient_view,
    delete_experience,
    doctor_profile_view,
    patient_profile_view,
    profile_redirect_view,
    update_doctor_image,
    update_doctor_profile,
    update_patient_profile,
    update_phone_ajax,
    add_experience
)

app_name = 'accounts'

urlpatterns = [
    # Authentication & Registration
    path('signup/', SignUpView.as_view(), name='signup'),  # User registration endpoint
    path('login/', MyLoginView.as_view(), name='login'),  # User login endpoint
    path('logout/', MyLogoutView.as_view(), name='logout'),  # User logout endpoint
    
    # Email Verification Activation
    path('activate/<str:uidb64>/<str:token>/', activate_account, name='activate_account'),  # Account activation via email link

    # Password Reset Flow
    path('password-reset/', MyPasswordResetView.as_view(), name='password_reset'),  # Request password reset email
    path('password-reset/done/', MyPasswordResetDoneView.as_view(), name='password_reset_done'),  # Password reset email sent notification
    path('password-reset-confirm/<uidb64>/<token>/', MyPasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # Enter new password form
    path('password-reset-complete/', MyPasswordResetCompleteView.as_view(), name='password_reset_complete'),  # Password reset success confirmation

    # Profile Management
    path('profile/', profile_redirect_view, name='profile'),  # Central profile routing based on user role (doctor/patient)
    path('profile/patient/', patient_profile_view, name='patient_profile'),  # Patient dashboard profile view
    path('profile/doctor/', doctor_profile_view, name='doctor_profile'),  # Doctor dashboard profile view
    path('profile/patient/update/', update_patient_profile, name='update_patient_profile'),  # Patient profile update form view
    path('profile/doctor/update/', update_doctor_profile, name='update_doctor_profile'),  # Doctor profile update form view

    # Profile Media Actions
        path('profile/update-image/', update_doctor_image, name='update_doctor_image'),  # Update doctor profile picture

    # AJAX Profile Phone Update 
    path('profile/update-phone/', update_phone_ajax, name='update_phone'),  # AJAX endpoint for updating phone number

    # Appointment Actions
    path('approve/<int:pk>/', approve_patient_view, name='approve_patient'),  # Approve patient appointment request
    path('cancel/<int:pk>/', cancel_patient_view, name='cancel_patient'),  # Cancel patient appointment request

    # Doctor Experience Management
    path('add-experience/', add_experience, name='add_experience'),  # Add professional experience for doctor
    path('delete-experience/<int:pk>/', delete_experience, name='delete_experience'),  # Delete professional experience by ID  
]