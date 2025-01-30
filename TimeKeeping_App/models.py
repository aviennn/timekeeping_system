from django.db import models
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.hashers import make_password


class Employee(models.Model):
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    joined_date = models.DateField(default=timezone.now)
    username = models.CharField(max_length=100, unique=True, editable=False)
    password = models.CharField(max_length=100, editable=False)

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

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TimeRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    lunch_start = models.TimeField(null=True, blank=True)
    lunch_end = models.TimeField(null=True, blank=True)

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

    @property
    def total_hours(self):
        if self.clock_in and self.clock_out:
            clock_in_dt = datetime.combine(self.date, self.clock_in)
            clock_out_dt = datetime.combine(self.date, self.clock_out)
            duration = clock_out_dt - clock_in_dt
            
            # Subtract lunch break if it exists
            if self.lunch_start and self.lunch_end:
                lunch_start_dt = datetime.combine(self.date, self.lunch_start)
                lunch_end_dt = datetime.combine(self.date, self.lunch_end)
                lunch_duration = lunch_end_dt - lunch_start_dt
                duration = duration - lunch_duration
            
            total_minutes = duration.total_seconds() / 60
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            
            if hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        return None

    def __str__(self):
        return f"TimeRecord for {self.employee} on {self.date}"
