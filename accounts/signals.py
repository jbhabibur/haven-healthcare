from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User, DoctorProfile, PatientProfile

# Imports required for generating secure email verification tokens and links
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


@receiver(post_save, sender=User)
def handle_user_registration_signals(sender, instance, created, **kwargs):
    """
    Triggers automatically when a new User instance is created.
    1. Handles automatic profile structure instantiation relative to selected roles.
    2. Compiles and sends a secure account activation link to the user's registered email.
    """
    if created:
        # Create matching specific sub-profile depending on user role
        if instance.role == User.Role.DOCTOR:
            DoctorProfile.objects.create(user=instance)
        elif instance.role == User.Role.PATIENT:
            PatientProfile.objects.create(user=instance)

        # Send activation token link if the registration contains an email address
        if instance.email:
            token = default_token_generator.make_token(instance)
            uid = urlsafe_base64_encode(force_bytes(instance.pk))
            
            # Reconstruct URL endpoint structure mapping to your verification path
            verification_url = f"http://127.0.0.1:8000/accounts/activate/{uid}/{token}/"
            
            subject = "Activate Your Haven Healthcare Account"
            message = (
                f"Hi {instance.username},\n\n"
                f"Thank you for signing up at Haven Healthcare. "
                f"To complete your registration, please verify your account by clicking the link below:\n"
                f"{verification_url}\n\n"
                f"If you did not initiate this request, you can safely disregard this email."
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@havenhealthcare.com')
            recipient_list = [instance.email]
            
            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            except Exception as e:
                # Log execution failures locally to assist console/terminal debugging
                print(f"SMTP Dispatch Error: Verification email could not be routed to {instance.email}. Reason: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """ Ensures child profiles are synchronized when the parent User model saves. """
    if instance.role == User.Role.DOCTOR and hasattr(instance, 'doctor_profile'):
        instance.doctor_profile.save()
    elif instance.role == User.Role.PATIENT and hasattr(instance, 'patient_profile'):
        instance.patient_profile.save()