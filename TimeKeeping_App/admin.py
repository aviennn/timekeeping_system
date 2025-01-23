from django.contrib import admin
from .models import Employee, TimeRecord

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'middle_name', 'last_name', 'email', 'joined_date', 'username', 'password')
    search_fields = ('first_name', 'last_name', 'email', 'username')
    list_filter = ('joined_date',)
    fields = ('first_name', 'middle_name', 'last_name', 'email', 'joined_date', 'username', 'password')
    readonly_fields = ('username', 'password')

admin.site.register(Employee, EmployeeAdmin)

admin.site.register(TimeRecord)
