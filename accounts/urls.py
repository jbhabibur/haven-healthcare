from django.urls import path
from .views import (
    SignUpView, 
    MyLoginView, 
    MyLogoutView, 
    MyPasswordResetView,
    MyPasswordResetDoneView,
    MyPasswordResetConfirmView,
    MyPasswordResetCompleteView
)

app_name = 'accounts'

urlpatterns = [
    # --- Authentication & Registration ---
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', MyLoginView.as_view(), name='login'),
    path('logout/', MyLogoutView.as_view(), name='logout'),

    # --- Password Reset Flow ---
    path('password-reset/', MyPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', MyPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', MyPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', MyPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]