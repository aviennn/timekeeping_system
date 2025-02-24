from django import forms
from .models import Employee
from .models import TimeRecord, transaction, EmployeeCounter
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
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'joined_date', 'employee_type', 'username']
        widgets = {
            'joined_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        if instance:
            # Interns: Make username read-only
            if instance.employee_type == 'Intern':
                self.fields['username'].widget.attrs['readonly'] = True

            # Employees: Disable changing back to Intern
            if instance.employee_type == 'Employee':
                self.fields['employee_type'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super().clean()
        employee_type = cleaned_data.get('employee_type')

        if self.instance and self.instance.pk:
            # When converting from Intern to Employee, generate a new username.
            if self.instance.employee_type == "Intern" and employee_type == "Employee":
                cleaned_data['username'] = self.generate_employee_username()
            elif self.instance.employee_type == "Employee":
                # Prevent Employees from changing back to Intern
                cleaned_data['employee_type'] = self.instance.employee_type

        return cleaned_data

    def generate_employee_username(self):
        """Generates the next available Employee username in sequence.
        For Employee type, the counter's year is set to None.
        """
        base_username = "M-100-"
        with transaction.atomic():
            latest_employee = Employee.objects.filter(username__startswith=base_username).order_by('-username').first()
            latest_number = int(latest_employee.username.split("-")[-1]) if latest_employee else 0

            # Use year=None for Employee type
            counter_obj, created = EmployeeCounter.objects.get_or_create(
                year=None,
                employee_type="Employee"
            )
            next_number = max(counter_obj.counter, latest_number) + 1
            return f"{base_username}{next_number:02d}"

    def clean_username(self):
        username = self.cleaned_data.get('username')
        employee_type = self.cleaned_data.get('employee_type')

        # For Interns, do not allow username editing.
        if self.instance and self.instance.employee_type == "Intern":
            return self.instance.username

        if employee_type == "Employee":
            base_username = "M-100-"

            try:
                new_number = int(username.split("-")[-1])
            except ValueError:
                raise forms.ValidationError("Invalid username format.")

            latest_employee = Employee.objects.filter(username__startswith=base_username).order_by('-username').first()
            latest_number = int(latest_employee.username.split("-")[-1]) if latest_employee else 0

            with transaction.atomic():
                # Use year=None for Employee type
                counter_obj, created = EmployeeCounter.objects.get_or_create(
                    year=None,
                    employee_type="Employee"
                )
                counter_obj.counter = max(counter_obj.counter, latest_number, new_number)
                counter_obj.save()

            return username

        return username

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