from django import forms
from .models import Employee
from .models import TimeRecord
from django.core.exceptions import ValidationError
from django.utils import timezone

class EmployeeCreationForm(forms.ModelForm):
    ALLOWED_EMAIL_DOMAINS = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
        "aol.com", "protonmail.com", "yandex.com", "mail.com", "zoho.com",
        "bulsu.edu.ph", "auf.edu.ph", "googlemail.com"
    ]

    class Meta:
        model = Employee
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'employee_type']

    employee_type = forms.ChoiceField(
        choices=Employee.EMPLOYEE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            domain = email.split('@')[-1]
            if domain not in self.ALLOWED_EMAIL_DOMAINS:
                raise ValidationError(f"Invalid email domain. Allowed domains: {', '.join(self.ALLOWED_EMAIL_DOMAINS)}")
        return email

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.joined_date = timezone.now().date()  # Set today's date
        if commit:
            employee.save()
        return employee

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        if self.instance and self.instance.pk:
            self.fields['employee_type'].initial = self.instance.employee_type

class EmployeeEditForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'joined_date', 'employee_type']
        widgets = {
            'joined_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        # If the employee is already an Employee type, disable the dropdown
        if self.instance and self.instance.pk and self.instance.employee_type == 'Employee':
            self.fields['employee_type'].widget.attrs['disabled'] = 'disabled'
            self.fields['employee_type'].widget.attrs['class'] = 'form-control disabled'

    def clean(self):
        cleaned_data = super().clean()
        # If the field is disabled in the form, make sure we keep the original value
        if self.instance and self.instance.pk and self.instance.employee_type == 'Employee':
            cleaned_data['employee_type'] = 'Employee'
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            allowed_domains = [
                "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
                "aol.com", "protonmail.com", "yandex.com", "mail.com", "zoho.com",
                "bulsu.edu.ph", "auf.edu.ph", "googlemail.com"
            ]
            domain = email.split('@')[-1]
            if domain not in allowed_domains:
                raise forms.ValidationError("Invalid email domain. Allowed domains: " + ", ".join(allowed_domains))
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
    
class TimeRecordCreationForm(forms.ModelForm):
    class Meta:
        model = TimeRecord
        fields = ['date','clock_in', 'clock_out', 'lunch_start', 'lunch_end']

    def save(self, commit=True):
        timerecord = super().save(commit=False)
        if commit:
            timerecord.save()
        return timerecord
    
class TimeRecordEditForm(forms.ModelForm):
    class Meta:
        model = TimeRecord
        fields = ['date', 'clock_in', 'clock_out', 'lunch_start', 'lunch_end']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'clock_in': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'clock_out': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'lunch_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'lunch_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

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