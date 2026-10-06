# core_app/admin.py
from django.contrib import admin
from .models import Profile, ReliefRequest

# Register the Profile model
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'full_name')
    list_filter = ('role',)
    search_fields = ('user__username', 'full_name', 'phone_number')

# Register the ReliefRequest model
@admin.register(ReliefRequest)
class ReliefRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'requester', 'request_type', 'status', 'assigned_to_volunteer', 'created_at')
    list_filter = ('status', 'request_type')
    search_fields = ('requester__username', 'description')
    list_editable = ('status', 'assigned_to_volunteer') # Allows direct editing from the list view!