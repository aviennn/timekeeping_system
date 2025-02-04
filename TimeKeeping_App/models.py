from django.db import models
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
import random
import string

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

class EmployeeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Employee(SoftDelete, models.Model):
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    joined_date = models.DateField(default=timezone.now)
    username = models.CharField(max_length=100, unique=True, editable=False)
    password = models.CharField(max_length=100)
    reset_code = models.CharField(max_length=6, null=True, blank=True)
    reset_code_expiry = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    
    objects = EmployeeManager()

    def save(self, *args, **kwargs):
        if not self.username:
            year = self.joined_date.year
            super().save(*args, **kwargs)
            formatted_id = f"{self.id:04d}"
            self.username = f"{year}-{self.last_name}{self.first_name}-{formatted_id}".replace(" ", "")
        
        if not self.password:
            self.password = make_password(self.username)

        if self.pk:  
            original = Employee.objects.get(pk=self.pk)
            if original.first_name != self.first_name or original.last_name != self.last_name:
                year = self.joined_date.year
                formatted_id = f"{self.id:04d}"
                self.username = f"{year}-{self.last_name}{self.first_name}-{formatted_id}".replace(" ", "")
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

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


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
            return 0

        total_minutes = 0

        # Case 1: Only clock in exists (no lunch, no clock out)
        if not self.lunch_start and not self.lunch_end and not self.clock_out:
            current_dt = datetime.combine(timezone.now().date(), timezone.now().time())
            clock_in_dt = datetime.combine(self.date, self.clock_in)
            total_minutes = (current_dt - clock_in_dt).total_seconds() / 60

        # Case 2: Clock in and lunch start exist (no lunch end)
        elif self.lunch_start and not self.lunch_end:
            return 0

        # Case 3: Full lunch break recorded
        elif self.lunch_start and self.lunch_end:
            clock_in_dt = datetime.combine(self.date, self.clock_in)
            lunch_start_dt = datetime.combine(self.date, self.lunch_start)
            lunch_end_dt = datetime.combine(self.date, self.lunch_end)
            
            if lunch_start_dt > clock_in_dt and lunch_end_dt > lunch_start_dt:
                # Calculate pre-lunch duration
                pre_lunch_minutes = (lunch_start_dt - clock_in_dt).total_seconds() / 60
                
                # If no clock_out but lunch is complete, count until lunch_end
                if not self.clock_out:
                    total_minutes = pre_lunch_minutes  # Only count time until lunch start
                else:
                    clock_out_dt = datetime.combine(self.date, self.clock_out)
                    if clock_out_dt > lunch_end_dt:
                        post_lunch_minutes = (clock_out_dt - lunch_end_dt).total_seconds() / 60
                    else:
                        post_lunch_minutes = 0
                    total_minutes = pre_lunch_minutes + post_lunch_minutes

        # Case 4: Clock in and clock out (no lunch)
        elif self.clock_out and not self.lunch_start:
            clock_in_dt = datetime.combine(self.date, self.clock_in)
            clock_out_dt = datetime.combine(self.date, self.clock_out)
            if clock_out_dt > clock_in_dt:
                total_minutes = (clock_out_dt - clock_in_dt).total_seconds() / 60

        return max(total_minutes, 0)

    def _get_daily_total_minutes(self):
        """Calculate total minutes worked for all records on this date"""
        daily_records = TimeRecord.objects.filter(
            employee=self.employee,
            date=self.date,
            is_deleted=False
        )
        
        total_minutes = 0
        for record in daily_records:
            total_minutes += record._calculate_record_minutes()
            
        return total_minutes

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
    def overtime_hours(self):
        """Calculate overtime based on all records for the day"""
        total_daily_minutes = self._get_daily_total_minutes()
        
        if total_daily_minutes > (8 * 60):  # Can be changed based on the hours needed per company
            overtime_minutes = total_daily_minutes - (8 * 60)
            hours = int(overtime_minutes // 60)
            minutes = int(overtime_minutes % 60)
            
            if hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        return None

    @property
    def lunch_break_duration(self):
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

    def __str__(self):
        return f"TimeRecord for {self.employee} on {self.date}"

