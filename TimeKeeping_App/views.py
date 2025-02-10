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
import requests
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
from .forms import TimeRecordEditForm
from .forms import TimeRecordCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import EmployeeEditForm



def dashboard(request):
    philippines_tz = pytz.timezone('Asia/Manila')
    current_time = timezone.now().astimezone(philippines_tz)
    current_employee = None
    error_message = None

    # Check if user is already logged in
    if 'current_employee_id' in request.session:
        try:
            current_employee = Employee.objects.get(id=request.session['current_employee_id'])
        except Employee.DoesNotExist:
            request.session.pop('current_employee_id', None)
            current_employee = None

    if request.method == 'POST':
        if not current_employee:  # Login process
            username_or_email = request.POST.get('username')
            password = request.POST.get('password')
            recaptcha_response = request.POST.get('g-recaptcha-response')

            # Verify reCAPTCHA before login
            recaptcha_verify = requests.post('https://www.google.com/recaptcha/api/siteverify', {
                'secret': settings.RECAPTCHA_PRIVATE_KEY,
                'response': recaptcha_response
            }).json()

            if not recaptcha_verify.get('success'):
                return render(request, 'dashboard.html', {
                    'error_message': 'Please complete the reCAPTCHA verification.',
                    'employees': Employee.objects.all(),
                    'current_datetime': current_time,
                })

            if username_or_email and password:
                employee = Employee.objects.filter(username=username_or_email).first()
                
                if not employee:
                    employee = Employee.objects.filter(email=username_or_email).first()

                if employee:
                    if check_password(password, employee.password):
                        request.session['current_employee_id'] = employee.id
                        return redirect('dashboard')
                    else:
                        error_message = 'Incorrect password. Please try again.'
                else:
                    error_message = 'Username or email not found. Please check your credentials.'



        if current_employee:  # Handle clock-in, clock-out, and lunch toggle
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
                    else:
                        error_message = 'You have already clocked in. Please clock out from your previous session first.'
                    
                elif action == 'clock_out':
                    if not latest_record or (latest_record and not latest_record.clock_in):
                        error_message = 'Please clock in first.'  #"Awaiting Status" and tries to clock out.
                    elif latest_record.clock_out:
                        error_message = 'Please clock in first.'  #  locked out and tries to clock out again.
                    elif latest_record.lunch_start and not latest_record.lunch_end:
                        error_message = 'Please end your lunch break before clocking out.'
                    else:
                        latest_record.clock_out = current_time.time()
                        latest_record.save()
                
                elif action == 'lunch_toggle' and latest_record:
                    if not latest_record.clock_in or latest_record.clock_out:
                        error_message = 'Please clock in before starting your lunch break.'
                    elif not latest_record.lunch_start:
                        latest_record.lunch_start = current_time.time()
                        latest_record.lunch_end = None
                        latest_record.save()
                    elif not latest_record.lunch_end:
                        latest_record.lunch_end = current_time.time()
                        latest_record.save()
                    else:
                        error_message = 'You have already taken your lunch break for today.'

                if create_new_record:
                    TimeRecord.objects.create(
                        employee=current_employee,
                        date=today,
                        clock_in=current_time.time()
                    )

    # Update user status
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

    return render(request, 'dashboard.html', {
        'employees': Employee.objects.all(),
        'current_employee': current_employee,
        'time_records': TimeRecord.objects.filter(employee=current_employee, date=today).order_by('-clock_in') if current_employee else [],
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

def overtime_duration(record):
    if record.overtime_hours:
        ht_duration = datetime.combine(record.date, record.overtime_hours)
        if ht_duration > 0:
            return ht_duration
    else: 
        return "N/A"

def format_readable_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")

def export_pdf(request, pk):
    current_employee = Employee.objects.get(id=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="employee_{current_employee.username}_time_records.pdf"'

    page_width, page_height = letter
    margin = 36
    content_width = page_width - (2 * margin)
    top_margin_for_table = 150  # Increased to accommodate new information
    bottom_margin = margin + 80
    right_margin = page_width - margin
    available_height = page_height - top_margin_for_table - bottom_margin


    p = canvas.Canvas(response, pagesize=letter)
    try:
        full_name = f"{current_employee.first_name} {current_employee.last_name}"
        start_date = request.GET.get('datefrom')
        end_date = request.GET.get('dateto')

        if start_date and end_date:
            records = TimeRecord.objects.filter(employee=current_employee, date__range=[start_date, end_date]).order_by('date')
        else:
            records = TimeRecord.objects.filter(employee=current_employee).order_by('date')

        # Logo and title drawing code
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

        # Employee name
        p.setFont("Helvetica-Bold", 12)
        employee_name_label_text = "Employee Name:"
        employee_name_label_width = p.stringWidth(employee_name_label_text, "Helvetica-Bold", 12)
        employee_name_label_y_position = subtitle_y_position - 25
        p.drawString((page_width - employee_name_label_width) / 2, employee_name_label_y_position, employee_name_label_text)
        
        p.setFont("Helvetica", 12)
        employee_name_width = p.stringWidth(full_name, "Helvetica", 12)
        employee_name_y_position = employee_name_label_y_position - 20
        p.drawString((page_width - employee_name_width) / 2, employee_name_y_position, full_name)

        # Date range
        date_range_y_position = employee_name_y_position - 25
        if start_date and end_date:
            date_range_text = f"Date Range: {format_readable_date(start_date)} to {format_readable_date(end_date)}"
        else:
            date_range_text = "All Records"
        
        p.setFont("Helvetica", 11)
        date_range_width = p.stringWidth(date_range_text, "Helvetica", 11)
        p.drawString((page_width - date_range_width) / 2, date_range_y_position, date_range_text)

        # Calculate total hours and overtime
        total_minutes = 0
        total_overtime_minutes = 0
        
        for record in records:
            if record.clock_in and record.clock_out:
                clock_in_dt = datetime.combine(record.date, record.clock_in)
                clock_out_dt = datetime.combine(record.date, record.clock_out)
                duration = clock_out_dt - clock_in_dt
                
                if record.lunch_start and record.lunch_end:
                    lunch_start_dt = datetime.combine(record.date, record.lunch_start)
                    lunch_end_dt = datetime.combine(record.date, record.lunch_end)
                    lunch_duration = lunch_end_dt - lunch_start_dt
                    duration = duration - lunch_duration
                
                total_minutes += duration.total_seconds() / 60

            # Fix for Overtime Calculation
            if record.overtime_hours:
                overtime_str = str(record.overtime_hours).strip().lower()
                
                try:
                    if "hour" in overtime_str or "minute" in overtime_str:
                        hours = 0
                        minutes = 0
                        
                        if "hour" in overtime_str:
                            hours = int(overtime_str.split("hour")[0].strip())
                        if "minute" in overtime_str:
                            minutes = int(overtime_str.split("minute")[0].split()[-1].strip())
                        
                        total_overtime_minutes += (hours * 60) + minutes

                    elif ":" in overtime_str:  # Handle "HH:MM" format
                        hours, minutes = map(int, overtime_str.split(':'))
                        total_overtime_minutes += (hours * 60) + minutes

                except (ValueError, IndexError):
                    print(f"Error parsing overtime for record {record.id}: {record.overtime_hours}")
                    continue


        # Table generation
        table_y_position = page_height - top_margin_for_table
        data = [["Date", "Clock In", "Clock Out", "Total Hours", "Overtime"]]
        for record in records:
            overtimeduration = record.overtime_hours if record.overtime_hours else "N/A"
            data.append([
                format_date(record.date),
                format_time(record.clock_in),
                format_time(record.clock_out),
                calculate_duration(record),
                overtimeduration
            ])
        
        rows_per_page = 25
        num_columns = len(data[0])
        column_width = content_width / num_columns
        
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
            ]))

            table.wrapOn(p, content_width, available_height)
            table.drawOn(p, margin, table_y_position - (len(table_chunk) * 20))

            start_row += rows_per_page
            if start_row < len(data):
                p.showPage()
                p.setFont("Helvetica", 11)
                
                # Reset position to avoid extra spacing
                table_y_position = page_height - margin  # Adjust this value

        # Format total hours
        total_hours = int(total_minutes // 60)
        remaining_minutes = int(total_minutes % 60)
        total_hours_text = f"{total_hours} hour{'s' if total_hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"

        # Format overtime hours
        overtime_hours = int(total_overtime_minutes // 60)
        overtime_minutes = int(total_overtime_minutes % 60)
        total_overtime_text = f"{overtime_hours} hour{'s' if overtime_hours != 1 else ''} {overtime_minutes} minute{'s' if overtime_minutes != 1 else ''}"

        table_bottom_y = table_y_position - (len(table_chunk) * 20)  # Adjusting space below table
        # Draw total hours and overtime below the table
        total_hours_y = table_bottom_y - 20
        overtime_y = total_hours_y - 20

        p.setFont("Helvetica-Bold", 11)
        total_hours_label = "Overall Total Hours:"
        total_overtime_label = "Overall Overtime Hours:"

        # Compute text width to center align
        total_hours_label_width = p.stringWidth(total_hours_label, "Helvetica-Bold", 11)
        total_overtime_label_width = p.stringWidth(total_overtime_label, "Helvetica-Bold", 11)

        total_hours_text_width = p.stringWidth(total_hours_text, "Helvetica", 11)
        total_overtime_text_width = p.stringWidth(total_overtime_text, "Helvetica", 11)

        # Calculate centered x-position
        total_hours_x = right_margin - total_hours_label_width - total_hours_text_width - 10
        total_overtime_x = right_margin - total_overtime_label_width - total_overtime_text_width - 10


        p.drawString(total_hours_x, total_hours_y, total_hours_label)
        p.drawString(total_overtime_x, overtime_y, total_overtime_label)

        p.setFont("Helvetica", 11)
        p.drawString(total_hours_x + total_hours_label_width + 10, total_hours_y, total_hours_text)
        p.drawString(total_overtime_x + total_overtime_label_width + 10, overtime_y, total_overtime_text)
            
        # Signatures
        signature_y = margin + 20
        center_x = page_width / 2
        line_width = 200
        employee_signature_x = center_x - (line_width + 40)
        supervisor_signature_x = center_x + 40

        p.line(employee_signature_x, signature_y, employee_signature_x + line_width, signature_y)
        p.line(supervisor_signature_x, signature_y, supervisor_signature_x + line_width, signature_y)
        
        p.drawString(employee_signature_x + 60, signature_y - 12, "Signature of Employee")
        p.drawString(supervisor_signature_x + 60, signature_y - 12, "Signature of Supervisor")
        
        p.save()
    except Employee.DoesNotExist:
        return HttpResponse("Employee not found", content_type="text/plain", status=404)

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
        recaptcha_response = request.POST.get('g-recaptcha-response')

        # Verify reCAPTCHA
        recaptcha_verify = requests.post('https://www.google.com/recaptcha/api/siteverify', {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': recaptcha_response
        }).json()

        if not recaptcha_verify.get('success'):
            error_message = "Please complete the reCAPTCHA verification."
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                error_message = "Invalid username or password."

    return render(request, 'admin_dashboard.html', {
        'employees': employees, 
        'is_authenticated': request.user.is_authenticated,
        'error_message': error_message,  # Always pass error_message
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
    logout(request)  
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
    total_minutes = 0
    total_overtime_minutes = 0

    for record in records:
        overtime_hours = record.overtime_hours if record.overtime_hours else "N/A"
        
        if record.overtime_hours:
            overtime_str = str(record.overtime_hours).strip().lower()
            try:
                if "hour" in overtime_str or "minute" in overtime_str:
                    hours = 0
                    minutes = 0
                    if "hour" in overtime_str:
                        hours = int(overtime_str.split("hour")[0].strip())
                    if "minute" in overtime_str:
                        minutes = int(overtime_str.split("minute")[0].split()[-1].strip())
                    total_overtime_minutes += (hours * 60) + minutes

                elif ":" in overtime_str:  # Handle "HH:MM" format
                    hours, minutes = map(int, overtime_str.split(':'))
                    total_overtime_minutes += (hours * 60) + minutes

            except (ValueError, IndexError):
                print(f"Error parsing overtime for record {record.id}: {record.overtime_hours}")
                overtime_hours = "N/A"  # fallback to "N/A"
        
        if record.clock_in and record.clock_out:
            clock_in_dt = datetime.combine(record.date, record.clock_in)
            clock_out_dt = datetime.combine(record.date, record.clock_out)
            duration = clock_out_dt - clock_in_dt
            
            if record.lunch_start and record.lunch_end:
                lunch_start_dt = datetime.combine(record.date, record.lunch_start)
                lunch_end_dt = datetime.combine(record.date, record.lunch_end)
                lunch_duration = lunch_end_dt - lunch_start_dt
                duration = duration - lunch_duration
            
            total_minutes += duration.total_seconds() / 60

        data.append({
            'Date': record.date,
            'Clock In': format_time(record.clock_in),
            'Clock Out': format_time(record.clock_out),
            'Lunch Break Hours': calculate_lunch_duration(record),
            'Total Hours': calculate_duration(record),
            'Overtime Hours': overtime_hours
        })
    
    total_hours = int(total_minutes // 60)
    remaining_minutes = int(total_minutes % 60)
    total_hours_text = f"{total_hours} hour{'s' if total_hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"

    total_overtime_hours = total_overtime_minutes // 60
    total_overtime_remaining_minutes = total_overtime_minutes % 60
    total_overtime_text = f"{total_overtime_hours} hour{'s' if total_overtime_hours != 1 else ''} {total_overtime_remaining_minutes} minute{'s' if total_overtime_remaining_minutes != 1 else ''}"

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="employee_{employee.username}_time_records.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Time Records')

        workbook = writer.book
        worksheet = writer.sheets['Time Records']
        worksheet.append(['', '', '', '', 'Overall Total Hours', 'Overall Total Overtime'])
        worksheet.append(['', '', '', '', total_hours_text, total_overtime_text])

    return response


@login_required(login_url='admin_dashboard')
def create_employee(request):
    if request.method == "POST":
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            # Check ALL existing emails, including deleted ones
            if Employee.objects.filter(email=email).exists():
                form.add_error('email', 'This email is already registered. Please use a different email address.')
            else:
                try:
                    employee = form.save(commit=False)
                    employee.is_deleted = False
                    employee.save()
                    messages.success(request, "Employee created successfully!")
                    return redirect("admin_dashboard")
                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")
        else:
            print(form.errors)  

        messages.error(request, "Failed to create employee. Please fix the errors in the form.")
    else:
        form = EmployeeCreationForm()

    employees = Employee.objects.filter(is_deleted=False)
    return render(request, "admin_dashboard.html", {
        "form": form,
        "employees": employees,
        "is_authenticated": request.user.is_authenticated 
    })

@login_required(login_url='admin_dashboard')
def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == "POST":
        form = EmployeeEditForm(request.POST, instance=employee)
        if form.is_valid():
            email = form.cleaned_data.get('email')

            # ✅ Fix: Allow current employee to keep their email
            if Employee.objects.filter(email=email).exclude(id=employee.id).exists():
                form.add_error('email', 'This email is already registered. Please use a different email address.')
            else:
                try:
                    form.save()
                    messages.success(request, "Employee updated successfully!")
                    return redirect("view_user_info", employee_id=employee.id)
                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")
        else:
            print(form.errors)  

        messages.error(request, "Failed to update employee. Please fix the errors in the form.")
    else:
        form = EmployeeEditForm(instance=employee)

    return render(request, "view_user_info.html", {
        "form": form,
        "employee": employee
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
        'error_message': error_message,
        'current_employee': employee
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
        form = TimeRecordEditForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('view_records', pk=record.employee.id) 
    else:
        form = TimeRecordEditForm(instance=record)

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
