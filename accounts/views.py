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
from .forms import CustomUserCreationForm

# --- Authentication & Registration ---

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/registration/signup.html'
    success_url = reverse_lazy('accounts:login') 

    def form_valid(self, form):
        # Saved instance triggers post_save signals for profile creation
        user = form.save()
        return super().form_valid(form)


class MyLoginView(LoginView):
    template_name = 'accounts/registration/login.html'

    def get_success_url(self):
        return reverse_lazy('home')


class MyLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


# --- Password Reset Flow ---

class MyPasswordResetView(PasswordResetView):
    template_name = 'accounts/registration/password_reset_form.html'
    email_template_name = 'accounts/registration/password_reset_email.html'
    html_email_template_name = 'accounts/registration/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class MyPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/registration/password_reset_done.html'


class MyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class MyPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/registration/password_reset_complete.html'