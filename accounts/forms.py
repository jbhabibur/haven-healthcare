from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import User, DoctorProfile, PatientProfile


# --- Custom User Creation Form (For Registration) ---
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


# --- Custom User Change Form (For Base Account Updates) ---
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role')


# --- Doctor Profile Form ---
class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        # The user link mapping field is excluded to prevent changing ownership profiles manually
        exclude = ('user',) 
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Cardiology'}),
            'qualification': forms.Textarea(attrs={'rows': 3}),
        }


# --- Patient Profile Form ---
class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        exclude = ('user',)
        widgets = {
            'medical_history': forms.Textarea(attrs={'rows': 3}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
        }