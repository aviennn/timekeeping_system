from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
import pytz
from .models import Employee, TimeRecord
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import redirect
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.http import HttpResponse
from datetime import datetime
from django.templatetags.static import static
from django.conf import settings
import os
import pandas as pd
from .forms import EmployeeCreationForm
from .models import Employee
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password

def dashboard(request):
    philippines_tz = pytz.timezone('Asia/Manila')
    current_time = timezone.now().astimezone(philippines_tz)
    current_employee = None

    if 'current_employee_id' in request.session:
        try:
            current_employee = Employee.objects.get(id=request.session['current_employee_id'])
        except Employee.DoesNotExist:
            current_employee = None

    if request.method == 'POST':
        if not current_employee:
            username = request.POST.get('username')
            password = request.POST.get('password')

            if username and password:
                try:
                    employee = Employee.objects.get(username=username)
                    if check_password(password, employee.password):
                        current_employee = employee
                        request.session['current_employee_id'] = employee.id
                        return redirect('dashboard')
                except Employee.DoesNotExist:
                    current_employee = None
                    request.session.pop('current_employee_id', None)

        if current_employee:
            action = request.POST.get('action')
            if action:
                today = current_time.date()
                latest_record = TimeRecord.objects.filter(
                    employee=current_employee,
                    date=today
                ).order_by('-clock_in').first()

                create_new_record = False
                if action == 'clock_in':
                    if not latest_record or latest_record.clock_out:
                        create_new_record = True
                    elif latest_record and not latest_record.clock_out:
                        
                        lunch_button_label = "Stop Lunch" if (latest_record.lunch_start and not latest_record.lunch_end) else "Start Lunch"
                        
                        return render(request, 'dashboard.html', {
                            'error_message': 'You have already clocked in. Please clock out from your previous session first.',
                            'employees': Employee.objects.all(),
                            'current_employee': current_employee,
                            'time_records': TimeRecord.objects.filter(employee=current_employee),
                            'current_datetime': current_time,
                            'status': 'Clocked In',
                            'lunch_button_label': lunch_button_label
                        })

                if create_new_record:
                    TimeRecord.objects.create(
                        employee=current_employee,
                        date=today,
                        clock_in=current_time.time()
                    )
                elif action == 'clock_out' and latest_record:
                    if not latest_record.clock_out:
                        latest_record.clock_out = current_time.time()
                        latest_record.save()
                elif action == 'lunch_toggle' and latest_record:
                    if not latest_record.lunch_start:
                        latest_record.lunch_start = current_time.time()
                        latest_record.lunch_end = None
                    elif not latest_record.lunch_end:
                        latest_record.lunch_end = current_time.time()
                    latest_record.save()

    if not current_employee and 'current_employee_id' in request.session:
        try:
            current_employee = Employee.objects.get(id=request.session['current_employee_id'])
        except Employee.DoesNotExist:
            current_employee = None


    status = "Pending"
    lunch_button_label = "Start Lunch"
    if current_employee:
        today = current_time.date()
        latest_record = TimeRecord.objects.filter(
            employee=current_employee,
            date=today
        ).order_by('-clock_in').first()

        if latest_record:
            if latest_record.clock_in and not latest_record.clock_out:
                status = "Clocked In"
            elif latest_record.clock_in and latest_record.clock_out:
                status = "Clocked Out"

            if latest_record.lunch_start and not latest_record.lunch_end:
                lunch_button_label = "Stop Lunch"
            elif latest_record.lunch_start and latest_record.lunch_end:
                lunch_button_label = "Start Lunch"

    return render(request, 'dashboard.html', {
        'employees': Employee.objects.all(),
        'current_employee': current_employee,
        'time_records': TimeRecord.objects.filter(employee=current_employee).order_by('-date', '-clock_in') if current_employee else [],
        'current_datetime': current_time,
        'status': status,
        'lunch_button_label': lunch_button_label
    })


def format_time(time_value):
    if time_value:
        return time_value.strftime("%I:%M:%S %p")
    return "N/A"

def format_date(date_value):
    return date_value.strftime("%B %d, %Y") if date_value else "N/A"


# Whole function is dedicated for human readable time, its painful to do
def calculate_duration(record):
    if record.clock_in and record.clock_out:
        clock_in_dt = datetime.combine(record.date, record.clock_in)
        clock_out_dt = datetime.combine(record.date, record.clock_out)
        duration = clock_out_dt - clock_in_dt
        
        # Subtract lunch break if it exists
        if record.lunch_start and record.lunch_end:
            lunch_start_dt = datetime.combine(record.date, record.lunch_start)
            lunch_end_dt = datetime.combine(record.date, record.lunch_end)
            lunch_duration = lunch_end_dt - lunch_start_dt
            duration = duration - lunch_duration
        
        total_minutes = duration.total_seconds() / 60
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return "N/A"

def calculate_lunch_duration(record):
    if record.lunch_start and record.lunch_end:
        lunch_start_dt = datetime.combine(record.date, record.lunch_start)
        lunch_end_dt = datetime.combine(record.date, record.lunch_end)
        duration = lunch_end_dt - lunch_start_dt
        total_minutes = duration.total_seconds() / 60
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return "N/A"

def export_pdf(request, pk):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="timerecords.pdf"'

    page_width, page_height = letter
    margin = 36
    content_width = page_width - (2 * margin)
    top_margin_for_table = 80

    p = canvas.Canvas(response, pagesize=letter)

    try:
        current_employee = Employee.objects.get(id=pk)
        records = TimeRecord.objects.filter(employee=current_employee)
        full_name = f"{current_employee.first_name} {current_employee.last_name}"

        icon_path = os.path.join(settings.BASE_DIR, 'TimeKeeping_App', 'static', 'images', 'icon-3.jpg')
        icon_x = margin
        icon_y = page_height - margin - 14

        p.setFont("Helvetica-Bold", 24)
        title_text = "Academe TS"
        title_width = p.stringWidth(title_text, "Helvetica-Bold", 24)
        title_x = (page_width - title_width) / 2

        spacing = 5
        image_width = 42
        title_width = p.stringWidth(title_text, "Helvetica-Bold", 31)
        total_width = image_width + spacing + title_width
        start_x = (page_width - total_width) / 2
        text_y = page_height - margin - 6

        p.drawImage(icon_path, start_x, icon_y, width=image_width, height=30)
        p.drawString(start_x + image_width + spacing, text_y, title_text)

        p.setFont("Helvetica", 12)
        subtitle_text = "GOCLOUD Asia, Inc."
        subtitle_width = p.stringWidth(subtitle_text, "Helvetica", 12)
        subtitle_y_position = page_height - margin - 25
        p.drawString((page_width - subtitle_width) / 2, subtitle_y_position, subtitle_text)

        p.setFont("Helvetica-Bold", 12)
        employee_name_label_text = "Employee Name:"
        employee_name_label_width = p.stringWidth(employee_name_label_text, "Helvetica-Bold", 12)
        employee_name_label_y_position = subtitle_y_position - 25
        p.drawString((page_width - employee_name_label_width) / 2, employee_name_label_y_position, employee_name_label_text)
        
        p.setFont("Helvetica", 12)
        employee_name_width = p.stringWidth(full_name, "Helvetica", 12)
        employee_name_y_position = employee_name_label_y_position - 20
        p.drawString((page_width - employee_name_width) / 2, employee_name_y_position, full_name)

        table_y_position = page_height - margin - top_margin_for_table
        
        data = [["Date", "Clock In", "Clock Out", "Total Hours"]]
        for record in records:
            data.append([
                format_date(record.date),
                format_time(record.clock_in),
                format_time(record.clock_out),
                calculate_duration(record)
            ])
        
        available_height = table_y_position - (margin + 20)
        rows_per_page = int(available_height / 20)
        
        start_row = 1
        while start_row < len(data):
            table_chunk = [data[0]] + data[start_row:start_row + rows_per_page]
            table = Table(table_chunk, colWidths=[content_width * 0.25] * 4)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ]))
            
            table.wrapOn(p, content_width, available_height)
            table.drawOn(p, margin, table_y_position - (len(table_chunk) * 20))
            
            start_row += rows_per_page
            if start_row < len(data):
                p.showPage()
                table_y_position = page_height - margin - top_margin_for_table
        
        signature_y = margin + 70
        center_x = page_width / 2
        line_width = 200
        employee_signature_x = center_x - (line_width + 40)
        supervisor_signature_x = center_x + 40

        p.line(employee_signature_x, signature_y, employee_signature_x + line_width, signature_y)
        p.line(supervisor_signature_x, signature_y, supervisor_signature_x + line_width, signature_y)

        employee_text_width = p.stringWidth("Signature of Employee", "Helvetica", 10)
        supervisor_text_width = p.stringWidth("Signature of Supervisor", "Helvetica", 10)

        employee_text_x = employee_signature_x + (line_width - employee_text_width) / 2.5
        supervisor_text_x = supervisor_signature_x + (line_width - supervisor_text_width) / 2.5

        p.drawString(employee_text_x, signature_y - 12, "Signature of Employee")
        p.drawString(supervisor_text_x, signature_y - 12, "Signature of Supervisor")
        
        p.save()
    except Employee.DoesNotExist:
        p.drawString(margin, page_height - margin, "No records were found.")
        p.save()

    return response


def logout_view(request):
    request.session.flush()  
    return redirect('dashboard')

def admin_dashboard(request):
    error_message = None
    employees = Employee.objects.all()  

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            error_message = "Invalid username or password."

    return render(request, 'admin_dashboard.html', {
        'employees': employees, 
        'is_authenticated': request.user.is_authenticated,
        'error_message': error_message,
    })

from django.shortcuts import render, get_object_or_404
from .models import TimeRecord, Employee
from django.http import HttpResponseForbidden

class EmployeeRecord(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return HttpResponseForbidden("You do not have permission to access this page.")

    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        
        datefrom = request.GET.get('datefrom')
        dateto = request.GET.get('dateto')

        if datefrom and dateto:
            time_records = TimeRecord.objects.filter(employee=employee, date__gte=datefrom, date__lte=dateto)
        else:
            time_records = TimeRecord.objects.filter(employee=employee)

        return render(request, "view_records.html", {
            "employee": employee, 
            "user": request.user,
            "is_authenticated": request.user.is_authenticated,
            "time_records": time_records
        })

    
def logout_admin(request):
    request.session.flush()  
    return redirect('admin_dashboard')

def export_excel(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    records = TimeRecord.objects.filter(employee=employee)

    data = []
    for record in records:
        data.append({
            'Date': record.date,
            'Clock In': format_time(record.clock_in),
            'Clock Out': format_time(record.clock_out),
            'Lunch Break Hours': calculate_lunch_duration(record),
            'Total Hours': calculate_duration(record)
        })
    
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="employee_{employee.username}_time_records.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Time Records')
    
    return response

def create_employee(request):
    if request.method == "POST":
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("admin_dashboard")  
    else:
        form = EmployeeCreationForm()

    employees = Employee.objects.all()
    return render(request, "admin_dashboard.html", {"form": form, "employees": employees})