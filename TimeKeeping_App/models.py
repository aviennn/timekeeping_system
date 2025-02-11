from django.db import models
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
import random
import string
from django.db import models
from django.contrib.auth.models import User  # Django's built-in User model
from django.utils.timezone import now

class SoftDelete(models.Model):
    is_deleted = models.BooleanField(default=False)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    def delete(self, *args, **kwargs):
        self.soft_delete()
        
    class Meta:
        abstract = True
        '''
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                condition=models.Q(is_deleted=False),
                name='unique_active_email'
            )
        ]
        '''
class EmployeeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Employee(SoftDelete, models.Model):
    EMPLOYEE_TYPE_CHOICES = [
        ('Employee', 'Employee'),
        ('Intern', 'Intern'),
    ]
        
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    joined_date = models.DateField(default=timezone.now)
    employee_type = models.CharField(max_length=10, choices=EMPLOYEE_TYPE_CHOICES)
    username = models.CharField(max_length=100, unique=True, editable=False)
    password = models.CharField(max_length=100)
    reset_code = models.CharField(max_length=6, null=True, blank=True)
    reset_code_expiry = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    
    objects = EmployeeManager()
    

    def generate_next_id(self):
        year = self.joined_date.year

        if self.employee_type == 'Intern':
            prefix = f"OJT-{year}-"
            existing_ids = Employee._base_manager.filter(
                username__startswith=prefix
            ).values_list('username', flat=True)
            
            numbers = [
                int(username.split('-')[-1]) 
                for username in existing_ids 
                if username.split('-')[-1].isdigit()
            ]
            next_number = max(numbers, default=0) + 1
            return f"{prefix}{next_number:03d}"

        elif self.employee_type == 'Employee':
            prefix = "M-100-"
            existing_ids = Employee._base_manager.filter(
                username__startswith=prefix
            ).values_list('username', flat=True)
            
            numbers = [
                int(username.split('-')[-1]) 
                for username in existing_ids 
                if username.split('-')[-1].isdigit()
            ]
            next_number = max(numbers, default=0) + 1
            return f"{prefix}{next_number:02d}"

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.generate_next_id()

        if not self.password:
            self.password = make_password(self.username)

        super().save(*args, **kwargs)
    
    def generate_reset_code(self):
            code = ''.join(random.choices(string.digits, k=6))
            self.reset_code = code
            self.reset_code_expiry = timezone.now() + timezone.timedelta(minutes=15)
            self.save()
            
            # Send email with reset code
            send_mail(
                'Password Reset Code',
                f'Your password reset code is: {code}\nThis code will expire in 15 minutes.',
                'academetsmain@gmail.com',
                [self.email],
                fail_silently=False,
            )
            return code

class TimeRecordManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class TimeRecord(SoftDelete, models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    lunch_start = models.TimeField(null=True, blank=True)
    lunch_end = models.TimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    
    objects = TimeRecordManager()

    
    def _calculate_record_minutes(self):
        """Calculate minutes worked for this specific record"""
        if not self.clock_in:
            return 0  # No clock-in, no work time

        total_minutes = 0

        # Case 1: No clock-out and no lunch-end, return 0
        if not self.clock_out and not self.lunch_end:
            return 0

        # Case 2: Clock-in + clock-out (no lunch recorded)
        if self.clock_out and not self.lunch_start:
            clock_in_dt = datetime.combine(self.date, self.clock_in)
            clock_out_dt = datetime.combine(self.date, self.clock_out)
            if clock_out_dt > clock_in_dt:
                total_minutes = (clock_out_dt - clock_in_dt).total_seconds() / 60

        # Case 3: Lunch start without lunch end → Return until lunch start
        elif self.lunch_start and not self.lunch_end:
            clock_in_dt = datetime.combine(self.date, self.clock_in)
            lunch_start_dt = datetime.combine(self.date, self.lunch_start)
            if lunch_start_dt > clock_in_dt:
                total_minutes = (lunch_start_dt - clock_in_dt).total_seconds() / 60

        # Case 4: Lunch recorded, but no clock-out → Calculate until lunch end
        elif self.lunch_start and self.lunch_end and not self.clock_out:
            clock_in_dt = datetime.combine(self.date, self.clock_in)
            lunch_start_dt = datetime.combine(self.date, self.lunch_start)
            lunch_end_dt = datetime.combine(self.date, self.lunch_end)

            if lunch_start_dt > clock_in_dt and lunch_end_dt > lunch_start_dt:
                pre_lunch_minutes = (lunch_start_dt - clock_in_dt).total_seconds() / 60
                total_minutes = pre_lunch_minutes

        # Case 5: Full lunch recorded and clock-out exists
        elif self.lunch_start and self.lunch_end and self.clock_out:
            clock_in_dt = datetime.combine(self.date, self.clock_in)
            lunch_start_dt = datetime.combine(self.date, self.lunch_start)
            lunch_end_dt = datetime.combine(self.date, self.lunch_end)
            clock_out_dt = datetime.combine(self.date, self.clock_out)

            if lunch_start_dt > clock_in_dt and lunch_end_dt > lunch_start_dt and clock_out_dt > lunch_end_dt:
                pre_lunch_minutes = (lunch_start_dt - clock_in_dt).total_seconds() / 60
                post_lunch_minutes = (clock_out_dt - lunch_end_dt).total_seconds() / 60
                total_minutes = pre_lunch_minutes + post_lunch_minutes

        return max(total_minutes, 0)

    def _get_daily_total_minutes_and_lunch(self):
        """Calculate total minutes worked and total lunch minutes for all records on this date"""
        daily_records = TimeRecord.objects.filter(
            employee=self.employee,
            date=self.date,
            is_deleted=False
        )
        
        total_minutes = 0
        total_lunch_minutes = 0
        
        for record in daily_records:
            total_minutes += record._calculate_record_minutes()
            if record.lunch_start and record.lunch_end:
                lunch_start_dt = datetime.combine(record.date, record.lunch_start)
                lunch_end_dt = datetime.combine(record.date, record.lunch_end)
                lunch_duration = (lunch_end_dt - lunch_start_dt).total_seconds() / 60
                total_lunch_minutes += lunch_duration
                
        return total_minutes, total_lunch_minutes

    @property
    def total_hours(self):
        """Calculate total hours for this specific record"""
        total_minutes = self._calculate_record_minutes()
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)

        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    @property
    def lunch_break_duration(self):
        """Calculate lunch break duration"""
        if self.lunch_start and self.lunch_end:
            lunch_start_dt = datetime.combine(self.date, self.lunch_start)
            lunch_end_dt = datetime.combine(self.date, self.lunch_end)
            duration = lunch_end_dt - lunch_start_dt
            total_minutes = duration.total_seconds() / 60
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            
            if hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        return None

    @property
    def overtime_hours(self):
        """Calculate overtime after subtracting lunch hours"""
        total_daily_minutes, total_lunch_minutes = self._get_daily_total_minutes_and_lunch()
        
        # Regular working hours (8 hours) in minutes
        regular_hours = 8 * 60
        
        # Calculate overtime by subtracting regular hours and lunch time
        overtime_minutes = total_daily_minutes - regular_hours
        
        if overtime_minutes > 0:
            hours = int(overtime_minutes // 60)
            minutes = int(overtime_minutes % 60)

            if hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        
        return None

    def __str__(self):
        return f"TimeRecord for {self.employee} on {self.date}"

class ActivityLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)  # Admins
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.CASCADE)  # Employees
    action = models.CharField(max_length=255)  # Description of action
    timestamp = models.DateTimeField()  # Set manually using NTP time

    def __str__(self):
        if self.user and self.user.is_superuser:
            return f"Admin {self.user.username} - {self.action} at {self.timestamp}"
        elif self.employee:
            return f"Employee {self.employee.username} - {self.action} at {self.timestamp}"
        return f"Unknown User - {self.action} at {self.timestamp}"


