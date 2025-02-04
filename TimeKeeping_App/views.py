from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
import pytz
from .models import Employee, TimeRecord
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph
from django.http import HttpResponse
from datetime import datetime
from django.templatetags.static import static
from django.conf import settings
import os
import pandas as pd
from .forms import EmployeeCreationForm
from .models import Employee
from django.contrib import messages  
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from .forms import ChangePasswordForm, ResetPasswordEmailForm, ResetPasswordForm
from .models import Employee
from django.contrib.auth.hashers import check_password
from .forms import TimeRecordForm
from .forms import TimeRecordCreationForm
from django.contrib.auth.decorators import login_required

def dashboard(request):
    philippines_tz = pytz.timezone('Asia/Manila')
    current_time = timezone.now().astimezone(philippines_tz)
    current_employee = None

    if 'current_employee_id' in request.session:
        try:
            current_employee = Employee.objects.get(id=request.session['current_employee_id'])
        except Employee.DoesNotExist:
            current_employee = None

    error_message = None

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
                        error_message = 'You have already clocked in. Please clock out from your previous session first.'

                elif action == 'clock_out' and latest_record:
                    if latest_record.lunch_start and not latest_record.lunch_end:
                        error_message = 'Please end your lunch break before clocking out.'
                    elif not latest_record.clock_out:
                        latest_record.clock_out = current_time.time()
                        latest_record.save()

                elif action == 'lunch_toggle':
                    if not latest_record or latest_record.clock_out:
                        error_message = 'Please clock in before starting your lunch break.'
                    else:
                        if not latest_record.lunch_start:
                            latest_record.lunch_start = current_time.time()
                            latest_record.lunch_end = None
                        elif not latest_record.lunch_end:
                            latest_record.lunch_end = current_time.time()
                        else:
                            error_message = 'You have already taken your lunch break for today.'
                        
                        if not error_message:
                            latest_record.save()

                if create_new_record:
                    TimeRecord.objects.create(
                        employee=current_employee,
                        date=today,
                        clock_in=current_time.time()
                    )

    if not current_employee and 'current_employee_id' in request.session:
        try:
            current_employee = Employee.objects.get(id=request.session['current_employee_id'])
        except Employee.DoesNotExist:
            current_employee = None

    status = "Awaiting Status"
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
        'lunch_button_label': lunch_button_label,
        'error_message': error_message
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
    top_margin_for_table = 36
    bottom_margin = margin + 50  # Space reserved for signatures
    max_table_height = page_height - 180 - bottom_margin  # Adjusted for header and footer

    p = canvas.Canvas(response, pagesize=letter)

    try:
        current_employee = Employee.objects.get(id=pk)
        full_name = f"{current_employee.first_name} {current_employee.last_name}"

        # Get date range from request
        start_date = request.GET.get('datefrom')
        end_date = request.GET.get('dateto')

        # Filter records based on date range
        if start_date and end_date:
            records = TimeRecord.objects.filter(employee=current_employee, date__range=[start_date, end_date]).order_by('date')
        else:
            records = TimeRecord.objects.filter(employee=current_employee).order_by('date')  # Default: All records


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

        # Add date range display
        if start_date and end_date:
            date_range_text = f"Date Range: {start_date} to {end_date}"
        else:
            date_range_text = "All Records"
        
        p.setFont("Helvetica", 11)
        date_range_width = p.stringWidth(date_range_text, "Helvetica", 11)
        p.drawString((page_width - date_range_width) / 2, employee_name_y_position - 20, date_range_text)


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

        # Calculate column width so they are equally spaced
        num_columns = len(data[0])  # 5 columns
        column_width = content_width / num_columns  # Evenly divide available width
        
        start_row = 1
        while start_row < len(data):
            table_chunk = [data[0]] + data[start_row:start_row + rows_per_page]
            table = Table(table_chunk, colWidths=[column_width] * num_columns)  
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
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
    request.session.pop('current_employee_id', None)  
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
        
        datefrom = request.GET.get('datefrom')
        dateto = request.GET.get('dateto')

        time_records = TimeRecord.objects.filter(employee=employee, is_deleted=False)

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
    
    start_date = request.GET.get('datefrom')
    end_date = request.GET.get('dateto')

    if start_date and end_date:
        records = TimeRecord.objects.filter(employee=employee, date__range=[start_date, end_date]).order_by('date')
    else:
        records = TimeRecord.objects.filter(employee=employee).order_by('date')  # Default: All records sorted by date

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

@login_required(login_url='admin_dashboard')
def create_employee(request):
    if request.method == "POST":
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee created successfully!")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Failed to create employee. Please fix the errors in the form.")
    else:
        form = EmployeeCreationForm()

    employees = Employee.objects.all()
    return render(request, "admin_dashboard.html", {
        "form": form,
        "employees": employees,
        "is_authenticated": request.user.is_authenticated 
    })


def create_timerecord(request, pk):
    employee = get_object_or_404(Employee, id=pk)  

    if request.method == "POST":
        form = TimeRecordCreationForm(request.POST)
        if form.is_valid():
            time_record = form.save(commit=False)  
            time_record.employee = employee  
            time_record.save()  
            messages.success(request, "Time record created successfully!")
            return redirect("view_records", pk=employee.id)  
    else:
        form = TimeRecordCreationForm()

    return render(request, "create_timerecord.html", {"form": form, "employee": employee})

def view_user_info(request, employee_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to access this page.")

    employee = get_object_or_404(Employee, id=employee_id)
    show_modal = False 

    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee details updated successfully!")
            return redirect('view_user_info', employee_id=employee.id)
        else:
            messages.error(request, "Failed to update employee. Please fix the errors in the form.")
            show_modal = True
            employee.refresh_from_db()
    else:
        form = EmployeeCreationForm(instance=employee)

    return render(request, 'view_user_info.html', {
        'employee': employee,
        'form': form,
        'show_modal': show_modal
    })

#def delete_employee(request, employee_id):
#    employee = get_object_or_404(Employee, id=employee_id)
    
#    employee.delete()

#    return redirect('admin_dashboard') 



def change_password(request):
    error_message = None
    employee_id = request.session.get('current_employee_id')

    if not employee_id:
        messages.error(request, "No employee found in session. Please log in.")
        return redirect('dashboard')

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found. Please contact admin.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']

            if not check_password(old_password, employee.password):
                error_message = 'Current password is incorrect.'
            elif new_password != confirm_password:
                error_message = 'New passwords do not match.'
            else:
                employee.password = make_password(new_password)
                employee.save()
                # Clear any existing messages before adding new one
                storage = messages.get_messages(request)
                storage.used = True
                messages.success(request, 'Password changed successfully!')
                return redirect('dashboard')
    else:
        form = ChangePasswordForm()

    return render(request, 'change_password.html', {
        'form': form,
        'error_message': error_message
    })

def forgot_password(request):
    error_message = None

    if request.method == 'POST':
        form = ResetPasswordEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                employee = Employee.objects.get(email=email)
                reset_code = employee.generate_reset_code()
                request.session['reset_email'] = email
                
                messages.success(request, 'Reset code has been sent to your email.')
                return redirect('reset_password')
            except Employee.DoesNotExist:
                error_message = 'No account found with this email.'
    else:
        form = ResetPasswordEmailForm()

    return render(request, 'forgot_password.html', {
        'form': form,
        'error_message': error_message
    })

def reset_password(request):
    error_message = None

    if 'reset_email' not in request.session:
        messages.error(request, 'Please provide your email first.')
        return redirect('forgot_password')

    email = request.session['reset_email']

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']

            try:
                employee = Employee.objects.get(
                    email=email,
                    reset_code=code,
                    reset_code_expiry__gt=timezone.now()
                )

                if new_password != confirm_password:
                    error_message = 'Passwords do not match.'
                else:
                    employee.password = make_password(new_password)
                    employee.reset_code = None
                    employee.reset_code_expiry = None
                    employee.save()

                    del request.session['reset_email']
                    messages.success(request, 'Password reset successfully!')
                    return redirect('dashboard')

            except Employee.DoesNotExist:
                error_message = 'Invalid or expired reset code.'
    else:
        form = ResetPasswordForm()

    return render(request, 'reset_password.html', {
        'form': form,
        'error_message': error_message
    })
    

def change_employee_password(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password and new_password == confirm_password:
            employee.password = make_password(new_password)
            employee.save()

            storage = messages.get_messages(request)
            storage.used = True

            messages.success(request, f"Password for {employee.first_name} {employee.last_name} has been updated successfully.")
            return redirect('admin_dashboard')  
        else:
            messages.error(request, "Passwords do not match. Please try again.")

    return render(request, 'change_employee_password.html', {'employee': employee})

def edit_time_record(request, pk):
    record = get_object_or_404(TimeRecord, pk=pk)
    
    if request.method == "POST":
        form = TimeRecordCreationForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('view_records', pk=record.employee.id) 
    else:
        form = TimeRecordCreationForm(instance=record)

    return render(request, 'edit_time_record.html', {'form': form, 'record': record})

def delete_time_record(request, pk):
    record = get_object_or_404(TimeRecord, pk=pk)
    record.soft_delete()
    messages.success(request, "Time record deleted successfully.")
    return redirect('view_records', pk=record.employee.id)


def delete_employee(request, pk):
    record = get_object_or_404(Employee, pk=pk)
    record.soft_delete()
    messages.success(request, "Employee record deleted successfully.")
    return redirect('admin_dashboard')