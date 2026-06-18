# appointments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import DoctorSlot, Appointment
from accounts.models import DoctorProfile, PatientProfile



#  DOCTOR SLOT VIEWS
class DoctorSlotListView(LoginRequiredMixin, ListView):
    """Allows doctors to view all of their created time slots"""
    model = DoctorSlot
    template_name = 'appointments/slot_list.html'
    context_object_name = 'slots'

    def get_queryset(self):
        # Filters slots exclusively for the currently logged-in doctor
        doctor_profile = get_object_or_404(DoctorProfile, user=self.request.user)
        return DoctorSlot.objects.filter(doctor=doctor_profile).order_by('date', 'start_time')


class DoctorSlotCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Allows doctors to create new available time slots"""
    model = DoctorSlot
    template_name = 'appointments/slot_form.html'
    fields = ['date', 'start_time', 'end_time']
    success_url = reverse_lazy('slot_list')

    def test_func(self):
        # Verifies if the authenticated user is actually a doctor
        return self.request.user.is_doctor

    def form_valid(self, form):
        # Automatically assigns the logged-in doctor's profile on successful form submission
        form.instance.doctor = get_object_or_404(DoctorProfile, user=self.request.user)
        return super().form_valid(form)


#  APPOINTMENT VIEWS
class AppointmentListView(LoginRequiredMixin, ListView):
    """Displays a list of appointments based on the authenticated user's role"""
    model = Appointment
    template_name = 'appointments/appointment_list.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        user = self.request.user
        if user.is_doctor:
            return Appointment.objects.filter(doctor__user=user).order_by('-created_at')
        elif user.is_patient:
            return Appointment.objects.filter(patient__user=user).order_by('-created_at')
        return Appointment.objects.none()


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """Displays the detailed view of a specific appointment"""
    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'


class BookAppointmentView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Allows authenticated patients to request or book an appointment with a doctor"""
    model = Appointment
    template_name = 'appointments/book_appointment.html'
    # 'doctor' and 'slot' fields are handled via URL query parameters and hidden inputs
    fields = ['preferred_date', 'preferred_time_notes', 'symptoms']
    success_url = reverse_lazy('appointments:appointment_list')

    # Essential to allow custom handling via handle_no_permission instead of instant 403 response
    raise_exception = True 

    def test_func(self):
        # Checks if the user is authenticated and possesses a patient role
        return self.request.user.is_authenticated and getattr(self.request.user, 'is_patient', False)

    def handle_no_permission(self):
        """Redirects unauthenticated users to login with a warning toast message instead of showing 403 Forbidden"""
        if not self.request.user.is_authenticated:
            # Adds a warning toast notification message for guest users
            messages.warning(self.request, "Please log in to your account first to book an online appointment.")
            return redirect('accounts:login') 
        
        # Adds an error toast if user is logged in but does not hold a patient role
        messages.error(self.request, "Only patient accounts are authorized to book appointment requests.")
        return redirect('appointments:doctor_list')

    def form_valid(self, form):
        doctor_id = self.request.POST.get('doctor')

        print("POST DATA =", self.request.POST)
        print("DOCTOR ID =", doctor_id)

        form.instance.doctor = get_object_or_404(
            DoctorProfile,
            id=doctor_id
        )

        form.instance.patient = get_object_or_404(
            PatientProfile,
            user=self.request.user
        )

        form.instance.status = 'PENDING'

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        # Passes the selected doctor data to the template to build an informative booking summary UI
        context = super().get_context_data(**kwargs)
        doctor_id = self.request.GET.get('doctor')
        if doctor_id:
            context['selected_doctor'] = get_object_or_404(DoctorProfile, id=doctor_id)
        return context



#  PUBLIC LIST/DETAIL VIEWS
class DoctorPublicListView(ListView):
    """Displays a public list of all available doctors"""
    model = DoctorProfile
    template_name = 'appointments/doctor_list.html'
    context_object_name = 'doctors'


class DoctorDetailView(DetailView):
    """Displays the profile and detailed specifications of a specific doctor"""
    model = DoctorProfile
    template_name = 'appointments/doctor_detail.html'
    context_object_name = 'doctor'