from django.urls import path
from .views import (
    SignUpView, 
    MyLoginView, 
    MyLogoutView, 
    MyPasswordResetView,
    MyPasswordResetDoneView,
    MyPasswordResetConfirmView,
    MyPasswordResetCompleteView,
    activate_account
)

from . import views

app_name = 'accounts'

urlpatterns = [
    # --- Authentication & Registration ---
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', MyLoginView.as_view(), name='login'),
    path('logout/', MyLogoutView.as_view(), name='logout'),
    
    # --- Email Verification Activation ---
    path('accounts/activate/<str:uidb64>/<str:token>/', activate_account, name='activate_account'),

    # --- Password Reset Flow ---
    path('password-reset/', MyPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', MyPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', MyPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', MyPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # --- Profile Management ---
    # Central profile endpoint that handles routing based on user roles
    path('profile/', views.profile_redirect_view, name='profile'),
    
    # Role-specific profile views
    path('profile/doctor/', views.doctor_profile_view, name='doctor_profile'),
    path('profile/patient/', views.patient_profile_view, name='patient_profile'),

    # --- AJAX & Other Actions ---
    path('profile/update-phone/', views.update_phone_ajax, name='update_phone'),
]