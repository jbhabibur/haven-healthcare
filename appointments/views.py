# appointments/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
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
    """Allows patients to request or book an appointment with a doctor"""
    model = Appointment
    template_name = 'appointments/book_appointment.html'
    fields = ['doctor', 'slot', 'preferred_date', 'preferred_time_notes', 'symptoms']
    success_url = reverse_lazy('appointment_list')

    def test_func(self):
        # Restricts access to ensure only patients can request appointments
        return self.request.user.is_patient

    def form_valid(self, form):
        # Automatically assigns the requesting patient's profile and sets default status
        form.instance.patient = get_object_or_404(PatientProfile, user=self.request.user)
        form.instance.status = 'PENDING'
        return super().form_valid(form)
    

class DoctorPublicListView(ListView):
    """Displays a public list of all available doctors"""
    model = DoctorProfile
    template_name = 'appointments/doctor_list.html'
    context_object_name = 'doctors'  # Used in the template within {% for doctor in doctors %}


class DoctorDetailView(DetailView):
    """Displays the profile and detailed specifications of a specific doctor"""
    model = DoctorProfile
    template_name = 'appointments/doctor_detail.html'
    context_object_name = 'doctor'