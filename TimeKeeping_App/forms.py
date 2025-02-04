from django import forms
from .models import Employee
from .models import TimeRecord

class EmployeeCreationForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'joined_date']

    def save(self, commit=True):
        employee = super().save(commit=False)
        if commit:
            employee.save()
        return employee

class TimeRecordForm(forms.ModelForm):
    class Meta:
        model = TimeRecord
        fields = ['date','clock_in', 'clock_out', 'lunch_start', 'lunch_end']


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput())
    new_password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

class ResetPasswordEmailForm(forms.Form):
    email = forms.EmailField()

class ResetPasswordForm(forms.Form):
    code = forms.CharField(max_length=6)
    new_password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())