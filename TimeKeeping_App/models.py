from django.db import models
from django.utils import timezone
from datetime import datetime


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
            self.username = f"{year}{self.last_name}{self.first_name}".replace(" ", "")
        
        if not self.password:
            self.password = self.username  

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TimeRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    morning_time_in = models.TimeField(null=True, blank=True)
    morning_time_out = models.TimeField(null=True, blank=True)
    afternoon_time_in = models.TimeField(null=True, blank=True)
    afternoon_time_out = models.TimeField(null=True, blank=True)

    @property
    def lunch_break_hours(self):
        if self.morning_time_out and self.afternoon_time_in:
            morning_out = datetime.combine(self.date, self.morning_time_out)
            afternoon_in = datetime.combine(self.date, self.afternoon_time_in)
            difference = afternoon_in - morning_out
            return round(difference.seconds / 3600, 2)
        return 0

    @property
    def total_hours(self):
        total = 0
        if self.morning_time_in and self.morning_time_out:
            morning = (
                timezone.datetime.combine(self.date, self.morning_time_out)
                - timezone.datetime.combine(self.date, self.morning_time_in)
            )
            total += morning.seconds / 3600
        if self.afternoon_time_in and self.afternoon_time_out:
            afternoon = (
                timezone.datetime.combine(self.date, self.afternoon_time_out)
                - timezone.datetime.combine(self.date, self.afternoon_time_in)
            )
            total += afternoon.seconds / 3600
        return round(total, 2)

    def __str__(self):
        return f"TimeRecord for {self.employee} on {self.date}"
