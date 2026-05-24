from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, DoctorProfile, PatientProfile

# ১. কাস্টম ইউজার ক্রিয়েশন ফর্ম (রেজিস্ট্রেশনের জন্য)
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # এখানে আপনি চাইলে স্টাইলিংয়ের জন্য Tailwind বা Bootstrap ক্লাস যোগ করতে পারেন
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'border rounded p-2 w-full'})

# ২. কাস্টম ইউজার এডিট ফর্ম (প্রোফাইল আপডেটের জন্য)
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role')

# ৩. ডাক্তার প্রোফাইল ফর্ম
class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        exclude = ('user',) # ইউজার ফিল্ডটি ইউজার নিজে এডিট করবে না, তাই বাদ দেওয়া হয়েছে
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Cardiology'}),
            'qualification': forms.Textarea(attrs={'rows': 3}),
        }

# ৪. পেশেন্ট প্রোফাইল ফর্ম
class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        exclude = ('user',)
        widgets = {
            'medical_history': forms.Textarea(attrs={'rows': 3}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
        }