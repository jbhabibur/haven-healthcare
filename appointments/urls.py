# appointments/urls.py
from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # --- Public Doctors List Page ---
    path('doctors/', views.DoctorPublicListView.as_view(), name='doctor_list'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),

    # --- Doctor Slots URLs ---
    path('slots/', views.DoctorSlotListView.as_view(), name='slot_list'),
    path('slots/create/', views.DoctorSlotCreateView.as_view(), name='slot_create'),

    # --- Appointment URLs ---
    path('', views.AppointmentListView.as_view(), name='appointment_list'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('book/', views.BookAppointmentView.as_view(), name='book_appointment'),
]