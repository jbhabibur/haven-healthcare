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
from .forms import CustomUserCreationForm
from .models import PatientProfile

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


# --- AJAX Profile Phone Update ---

@login_required
@require_POST
def update_phone_ajax(request):
    """
    অ্যাপয়েন্টমেন্ট পেজ থেকে লগইন করা পেশেন্টের ফোন নাম্বার 
    AJAX এর মাধ্যমে তাৎক্ষণিক আপডেট করার ভিউ।
    """
    try:
        data = json.loads(request.body)
        new_phone = data.get('phone_number', '').strip()
        
        if not new_phone:
            return JsonResponse({'success': False, 'error': 'ফোন নাম্বার খালি রাখা যাবে না।'}, status=400)
            
        # পেশেন্টের প্রোফাইল খুঁজে বের করা বা না থাকলে তৈরি করা
        profile, created = PatientProfile.objects.get_or_create(user=request.user)
        
        # নতুন নাম্বার সেট করে মডেল ভ্যালিডেশন রান করানো (Regex & Unique চেক করার জন্য)
        profile.phone_number = new_phone
        profile.full_clean() 
        profile.save()
        
        return JsonResponse({'success': True, 'phone_number': profile.phone_number})
        
    except ValidationError as e:
        # মডেলের RegexValidator বা unique ট্রিলারে যে এরর আসবে তা ফ্রন্টএন্ডে পাঠানো
        error_msg = e.message_dict.get('phone_number', ['ভুল ডাটা দেওয়া হয়েছে।'])[0]
        return JsonResponse({'success': False, 'error': error_msg}, status=400)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'সার্ভারে কোনো সমস্যা হয়েছে। আবার চেষ্টা করুন।'}, status=500)