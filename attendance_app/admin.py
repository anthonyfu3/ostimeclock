from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Punch, CustomUser, TimeclockBox, DailyHours, WeeklyHours

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'employee_number', 'is_staff', 'is_active',)
    list_filter = ('user_type', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'employee_number', 'groups')}),
        ('Permissions', {'fields': ('user_type', 'is_staff', 'is_active')}),
    )

@admin.register(Punch)
class PunchAdmin(admin.ModelAdmin):
    list_display = ('user', 'punch_type', 'timestamp')
    list_filter = ('punch_type', 'timestamp')
    search_fields = ('user__username', 'timestamp')

@admin.register(TimeclockBox)
class TimeclockBoxAdmin(admin.ModelAdmin):
    list_display = ('box_id', 'location', 'last_connected')
    search_fields = ('box_id', 'location')
    list_filter = ('location',)

@admin.register(DailyHours)
class DailyHoursAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'total_hours']
    search_fields = ['user__username', 'date']
    list_filter = ['user', 'date']

@admin.register(WeeklyHours)
class WeeklyHoursAdmin(admin.ModelAdmin):
    list_display = ['user', 'week_start_date', 'total_hours']
    search_fields = ['user__username', 'week_start_date']
    list_filter = ['user', 'week_start_date']