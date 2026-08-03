# appointments/views.py

from datetime import datetime, timedelta
import json

# Django Core & Shortcut Imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone

# Django Database & Functions
from django.db.models import Q, Value
from django.db.models.functions import Concat

# Django Generic Class-Based Views
from django.views.generic import CreateView, DetailView, ListView, UpdateView

# Local App Models & Profiles
from accounts.models import DoctorProfile, PatientProfile
from .models import Appointment, DoctorSlot


# Public & Profile Views
class DoctorPublicListView(ListView):
    model = DoctorProfile
    template_name = 'appointments/doctor_list.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '').strip()
        
        if search_query:
            queryset = queryset.annotate(
                full_name=Concat('user__first_name', Value(' '), 'user__last_name')
            ).filter(
                Q(full_name__icontains=search_query) | 
                Q(user__first_name__icontains=search_query) | 
                Q(user__last_name__icontains=search_query) |
                Q(specialization__icontains=search_query)
            )
        return queryset

class DoctorDetailView(DetailView):
    model = DoctorProfile
    template_name = 'appointments/doctor_detail.html'
    context_object_name = 'doctor'

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return get_object_or_404(DoctorProfile, user__username=username)




# Appointment Management
class AppointmentListView(LoginRequiredMixin, ListView):
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
    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'

class BookAppointmentView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Appointment
    template_name = 'appointments/book_appointment.html'
    fields = ['notes', 'symptoms']
    success_url = reverse_lazy('appointments:appointment_list')

    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'patient_profile')

    def form_valid(self, form):
        doctor_id = self.request.POST.get('doctor')
        slot_id = self.request.POST.get('slot')
        patient_phone = self.request.POST.get('patient_phone')

        # Update patient phone number
        patient_profile = self.request.user.patient_profile
        if patient_phone:
            patient_profile.phone_number = patient_phone
            patient_profile.save()

        appointment = form.save(commit=False)
        appointment.patient = patient_profile
        appointment.doctor = get_object_or_404(DoctorProfile, user__username=doctor_id)
        
        # slot_id is checked to ensure it's not None or 'custom' before proceeding
        if slot_id and slot_id != 'custom':
            slot = get_object_or_404(DoctorSlot, id=slot_id, is_booked=False)
            appointment.slot = slot
            appointment.status = 'CONFIRMED'
            slot.is_booked = True
            slot.save()
        
        appointment.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the doctor's username from the GET parameters
        doctor_username = self.request.GET.get('doctor')
        
        if doctor_username:
            User = get_user_model()
            doctor_user = User.objects.filter(username=doctor_username).first()
            # Pass the doctor's name to the context
            context['doctor_name'] = str(doctor_user) if doctor_user else "Unknown Doctor"
        else:
            context['doctor_name'] = "Unknown Doctor"
            
        return context




# Doctor Slots
class DoctorSlotListView(LoginRequiredMixin, ListView):
    model = DoctorSlot
    template_name = 'appointments/slot_list.html'
    context_object_name = 'slots'

    def get_queryset(self):
        # Filters slots exclusively for the currently logged-in doctor
        doctor_profile = get_object_or_404(DoctorProfile, user=self.request.user)
        return DoctorSlot.objects.filter(doctor=doctor_profile).order_by('date', 'start_time')

@login_required
def create_slots(request):
    if request.method == 'POST':
        try:
            start_date_str = request.POST.get('start_date')
            weeks = int(request.POST.get('weeks', 1))
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            doctor = DoctorProfile.objects.get(user=request.user)
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            slots_created = 0

            for i in range(weeks):
                slot_date = start_date + timedelta(weeks=i)
                obj, created = DoctorSlot.objects.get_or_create(
                    doctor=doctor, date=slot_date, start_time=start_time, end_time=end_time
                )
                if created:
                    slots_created += 1

            if slots_created > 0:
                msg = f"{slots_created} new slots created!"
                msg_type = "success"
                messages.success(request, msg)
            else:
                msg = "No new slots created (they already exist)."
                msg_type = "warning"
                messages.warning(request, msg)
            
            response = redirect('accounts:doctor_profile')
            # HTMX Trigger
            response['HX-Trigger'] = json.dumps({"toast": {"message": msg, "type": msg_type}})
            return response

        except Exception as e:
            msg = f"Error: {str(e)}"
            messages.error(request, msg)
            response = redirect('accounts:doctor_profile')
            response['HX-Trigger'] = json.dumps({"toast": {"message": msg, "type": "error"}})
            return response
    return redirect('accounts:doctor_profile')




@login_required
def delete_slot(request, slot_id):
    slot = get_object_or_404(DoctorSlot, id=slot_id, doctor=request.user.doctor_profile)
    
    if not slot.is_booked:
        slot.delete()
        msg = "Slot deleted successfully!"
        msg_type = "success"
        messages.success(request, msg)
    else:
        msg = "Cannot delete a booked slot!"
        msg_type = "error"
        messages.error(request, msg)
    
    response = redirect('accounts:doctor_profile')
    # HTMX Trigger
    response['HX-Trigger'] = json.dumps({"toast": {"message": msg, "type": msg_type}})
    return response

def check_slots(request):
    doctor_username = request.GET.get('doctor')
    if not doctor_username:
        return JsonResponse({'slots': []})

    today = timezone.now().date()
    print("First check,", doctor_username)

    all_slots_of_doctor = DoctorSlot.objects.filter(
        doctor__user__username=doctor_username
    )
    print("object", DoctorSlot.objects)

    slots_list = list(DoctorSlot.objects.values())
    print("list", slots_list)

    context = {
        'slots_list': slots_list,
    }

    print("meme", slots_list)

    return render(request, 'includes/slots_partial.html', context)