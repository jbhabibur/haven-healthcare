# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import User, DoctorProfile, PatientProfile
from django import forms
from django.forms import inlineformset_factory
from .models import User, DoctorProfile, DoctorExperience
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.forms import AuthenticationForm


#  Custom User Creation Form (For Registration)
class CustomUserCreationForm(UserCreationForm):
    # Explicitly enforce email as a required field
    email = forms.EmailField(required=True, help_text="Required. A valid email address.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically inject basic styling classes into all rendered form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'border rounded p-2 w-full'})

        self.fields['username'].widget.attrs.update({
            'class': 'border rounded p-2 w-full',
            'placeholder': 'Enter your username'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'border rounded p-2 w-full',
            'placeholder': 'example@email.com'
        })
        self.fields['role'].widget.attrs.update({
            'class': 'border rounded p-2 w-full'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'border rounded p-2 w-full',
            'placeholder': 'First Name'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'border rounded p-2 w-full',
            'placeholder': 'Last Name'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'border rounded p-2 w-full',
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'border rounded p-2 w-full',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):
        """
        Validates that the provided email address is unique across the platform.
        Performs a case-insensitive lookup to block duplicate account creation.
        """
        email = self.cleaned_data.get('email')
        if email:
            # Check if any user profile already claims this specific email address
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError("A user with this email address already exists.")
        
        return email


# Custom User Change Form (For Base Account Updates)
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role')


# Doctor Profile Form
class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = [
            'image', 'specialization', 'qualification', 'specialty_description', 
            'registration_number', 'doctor_info', 'consultation_fee', 
            'follow_up_fee', 'follow_up_validity_days', 'is_available'
        ]
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Cardiology'}),
            'qualification': forms.Textarea(attrs={'rows': 3}),
        }


# Patient Profile Form
class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        exclude = ('user',)
        widgets = {
            'medical_history': forms.Textarea(attrs={'rows': 3}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
        }


# User Update Form (For Updating Basic User Info)
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


# Doctor Profile Update Form
class DoctorProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['image', 'specialization', 'qualification', 'specialty_description', 'doctor_info', 'consultation_fee', 'follow_up_fee']


# Doctor Experience FormSet for Inline Editing
ExperienceFormSet = inlineformset_factory(
    DoctorProfile, 
    DoctorExperience, 
    fields=('institution_name', 'designation', 'department', 'start_date', 'end_date'),
    extra=1, 
    can_delete=True
)


# Custom Login Form with Enhanced Styling
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'border border-gray-300 rounded-lg p-3 w-full focus:outline-none focus:ring-2 focus:ring-blue-500',
            })
            
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Enter your username'
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': '••••••••'
        })


# Password Reset Request Form (For Email Submission)
class MyPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'border rounded p-2 w-full',
            'placeholder': 'Enter your registered email'
        })


# New Password Set Form (After Clicking the Link)
class MySetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'border rounded p-2 w-full',
            })
        self.fields['new_password1'].widget.attrs.update({'placeholder': 'Enter new password'})
        self.fields['new_password2'].widget.attrs.update({'placeholder': 'Confirm new password'})