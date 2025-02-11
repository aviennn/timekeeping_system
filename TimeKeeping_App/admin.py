from django.contrib import admin
from .models import Employee, TimeRecord
from django import forms
from django.contrib.auth.hashers import make_password

class EmployeeAdminForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an existing Employee type, disable the dropdown
        if self.instance and self.instance.pk and self.instance.employee_type == 'Employee':
            self.fields['employee_type'].disabled = True
            self.fields['employee_type'].help_text = 'Employee type cannot be changed once set to Employee.'

    def clean(self):
        cleaned_data = super().clean()
        # If the instance exists and is an Employee, enforce the employee type
        if self.instance and self.instance.pk and self.instance.employee_type == 'Employee':
            cleaned_data['employee_type'] = 'Employee'
        return cleaned_data

class EmployeeAdmin(admin.ModelAdmin):
    form = EmployeeAdminForm
    list_display = ('username', 'first_name', 'middle_name', 'last_name', 'email', 'joined_date', 'employee_type')
    search_fields = ('first_name', 'last_name', 'email', 'username')
    list_filter = ('joined_date', 'employee_type')
    fields = ('employee_type', 'first_name', 'middle_name', 'last_name', 'email', 'joined_date', 'username', 'password')
    readonly_fields = ('username', 'password')

    def save_model(self, request, obj, form, change):
        if change:  # If this is an edit (not a new employee)
            old_instance = self.model.objects.get(pk=obj.pk)
            old_type = old_instance.employee_type
            new_type = form.cleaned_data.get('employee_type')

            # If changing from Intern to Employee
            if old_type == 'Intern' and new_type == 'Employee':
                # Save first to ensure we have a pk
                super().save_model(request, obj, form, change)
                
                # Update username and password
                new_username = f"M-100-{obj.pk:02d}"
                obj.username = new_username
                obj.password = make_password(new_username)
                obj.save()

                # Add a message to the user
                from django.contrib import messages
                messages.info(request, f'Username and password have been updated to: {new_username}')
            else:
                super().save_model(request, obj, form, change)
        else:
            # For new employees, just save normally
            super().save_model(request, obj, form, change)

class TimeRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'clock_in', 'clock_out', 'lunch_start', 'lunch_end')
    search_fields = ('employee__username', 'date')

admin.site.register(Employee, EmployeeAdmin)

admin.site.register(TimeRecord, TimeRecordAdmin)