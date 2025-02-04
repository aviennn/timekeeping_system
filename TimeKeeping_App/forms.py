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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    
class TimeRecordCreationForm(forms.ModelForm):
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

    def save(self, commit=True):
        timerecord = super().save(commit=False)
        if commit:
            timerecord.save()
        return timerecord
    
class TimeRecordForm(forms.ModelForm):
    class Meta:
        model = TimeRecord
        fields = ['date','clock_in', 'clock_out', 'lunch_start', 'lunch_end']
    
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