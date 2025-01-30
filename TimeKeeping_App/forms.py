from django import forms
from .models import Employee

class EmployeeCreationForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'joined_date']

    def save(self, commit=True):
        employee = super().save(commit=False)
        if commit:
            employee.save()
        return employee

class EmployeeUpdateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'joined_date']

    def save(self, commit=True):
        employee = super().save(commit=False)
        if commit:
            employee.save()
        return employee