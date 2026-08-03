# appointments/admin.py
from django.contrib import admin
from .models import DoctorSlot, Appointment

# DoctorSlot Admin
@admin.register(DoctorSlot)
class DoctorSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_booked')
    list_filter = ('date', 'is_booked', 'doctor')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name')


# --- Appointment Admin ---
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'patient', 'doctor', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = (
        'patient__user__username', 
        'doctor__user__username', 
        'symptoms'
    )

    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Profiles', {
            'fields': ('patient', 'doctor', 'slot')
        }),
        ('Appointment Details', {
            'fields': ('symptoms', 'notes') 
        }),
        ('Status', {
            'fields': ('status', 'created_at')
        }),
    )