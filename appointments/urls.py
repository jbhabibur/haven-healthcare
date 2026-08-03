# appointments/urls.py

from django.urls import path
from .views import (
    DoctorPublicListView,
    DoctorDetailView,
    AppointmentListView,
    AppointmentDetailView, 
    BookAppointmentView,
    DoctorSlotListView,
    create_slots,
    delete_slot,
    check_slots,
)

app_name = 'appointments'

urlpatterns = [
    # Public & Profile Views
    path('doctors/', DoctorPublicListView.as_view(), name='doctor_list'),
    path('doctor/<str:username>/', DoctorDetailView.as_view(), name='doctor_detail'),

    # Appointment Management
    path('', AppointmentListView.as_view(), name='appointment_list'),
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment_detail'),
    path('book/', BookAppointmentView.as_view(), name='book_appointment'),

    # Doctor Slots
    path('slots/', DoctorSlotListView.as_view(), name='slot_list'),
    path('create-slots/', create_slots, name='create_slots'),
    path('delete-slot/<int:slot_id>/', delete_slot, name='delete_slot'),
    path('check-slots/', check_slots, name='check_slots'),
]