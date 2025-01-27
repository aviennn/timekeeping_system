from django.contrib import admin
from .models import Employee, TimeRecord

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'middle_name', 'last_name', 'email', 'joined_date', 'username', 'password')
    search_fields = ('first_name', 'last_name', 'email', 'username')
    list_filter = ('joined_date',)
    fields = ('first_name', 'middle_name', 'last_name', 'email', 'joined_date', 'username', 'password')
    readonly_fields = ('username', 'password')

class TimeRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'clock_in', 'clock_out', 'lunch_start', 'lunch_end')
    search_fields = ('employee__username', 'date')

admin.site.register(Employee, EmployeeAdmin)

admin.site.register(TimeRecord, TimeRecordAdmin)
