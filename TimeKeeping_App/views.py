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

def dashboard(request):
    philippines_tz = pytz.timezone('Asia/Manila')
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        password = request.POST.get('password')
        
        if employee_id and password:
            try:
                current_employee = Employee.objects.get(id=employee_id, password=password)
                request.session['current_employee_id'] = current_employee.id
                
                action = request.POST.get('action')
                
                if action:
                    current_time = timezone.now().astimezone(philippines_tz)
                    record, created = TimeRecord.objects.get_or_create(
                        employee=current_employee,
                        date=current_time.date()
                    )
                    
                    if action == 'morning_in':
                        record.morning_time_in = current_time.time()
                    elif action == 'morning_out':
                        record.morning_time_out = current_time.time()
                    elif action == 'afternoon_in':
                        record.afternoon_time_in = current_time.time()
                    elif action == 'afternoon_out':
                        record.afternoon_time_out = current_time.time()
                    
                    record.save()
            except Employee.DoesNotExist:
                current_employee = None
                request.session.pop('current_employee_id', None)
        else:
            request.session.pop('current_employee_id', None)
    else:
        current_employee = None
        request.session.pop('current_employee_id', None)
    
    return render(request, 'dashboard.html', {
        'employees': Employee.objects.all(),
        'current_employee': current_employee,
        'time_records': TimeRecord.objects.filter(employee=current_employee) if current_employee else [],
        'current_datetime': timezone.now().astimezone(philippines_tz)
    })

def format_time(time_value):
    if time_value:
        return time_value.strftime("%I:%M:%S %p")
    return "N/A"

def format_date(date_value):
    return date_value.strftime("%B %d, %Y") if date_value else "N/A"

def format_hours(total_hours):
    hours = int(total_hours)
    minutes = round((total_hours - hours) * 60)
    return f"{hours} hours and {minutes} minutes"

def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="timerecords.pdf"'
    
    page_width, page_height = letter
    margin = 36
    content_width = page_width - (2 * margin)
    top_margin_for_table = 80
    
    p = canvas.Canvas(response, pagesize=letter)
    
    current_employee_id = request.session.get('current_employee_id')
    
    if current_employee_id:
        try:
            current_employee = Employee.objects.get(id=current_employee_id)
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
            employee_name_text = full_name
            employee_name_width = p.stringWidth(employee_name_text, "Helvetica", 12)
            employee_name_y_position = employee_name_label_y_position - 20
            p.drawString((page_width - employee_name_width) / 2, employee_name_y_position, employee_name_text)

            table_y_position = employee_name_y_position - top_margin_for_table

            data = [["Date", "Morning", "Afternoon", "Total Hours"]]
            
            for record in records:
                data.append([
                    format_date(record.date),
                    f"{format_time(record.morning_time_in)} - {format_time(record.morning_time_out)}",
                    f"{format_time(record.afternoon_time_in)} - {format_time(record.afternoon_time_out)}",
                    format_hours(record.total_hours)
                ])
            
            table = Table(data, colWidths=[content_width * 0.25, content_width * 0.25, content_width * 0.25, content_width * 0.25])
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
            
            table_width, table_height = table.wrap(0, 0)
            table_x = (page_width - table_width) / 2
            table_y = table_y_position

            table.drawOn(p, table_x, table_y)

            signature_y = table_y - 50

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

        except Employee.DoesNotExist:
            p.drawString(margin, page_height - margin, "No records were found.")
    else:
        p.drawString(margin, page_height - margin, "No employee entries found.")
    
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

class EmployeeRecord(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return HttpResponseForbidden("You do not have permission to access this page.")

    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        time_records = TimeRecord.objects.filter(employee=employee)
        return render(request, "view_records.html", {"employee": employee, "time_records": time_records})
    
def logout_admin(request):
    request.session.flush()  
    return redirect('admin_dashboard')