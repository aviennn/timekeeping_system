from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
import pytz
from .models import Employee, TimeRecord
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import redirect

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




def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="timerecords.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    
    # Retrieve the logged-in employee from the session
    current_employee_id = request.session.get('current_employee_id')
    
    if current_employee_id:
        try:
            current_employee = Employee.objects.get(id=current_employee_id)
            records = TimeRecord.objects.filter(employee=current_employee)
            
            y = 750
            # Concatenate first and last names for the employee
            full_name = f"{current_employee.first_name} {current_employee.last_name}"
            p.drawString(100, y, f"Time Records for {full_name}")
            y -= 30
            
            for record in records:
                p.drawString(100, y, f"Date: {record.date}")
                p.drawString(100, y-20, f"Morning: {record.morning_time_in or 'N/A'} - {record.morning_time_out or 'N/A'}")
                p.drawString(100, y-40, f"Afternoon: {record.afternoon_time_in or 'N/A'} - {record.afternoon_time_out or 'N/A'}")
                p.drawString(100, y-60, f"Total Hours: {record.total_hours}")
                y -= 100
                
                if y < 100:
                    p.showPage()
                    y = 750
        except Employee.DoesNotExist:
            p.drawString(100, 750, "No records found")
    else:
        p.drawString(100, 750, "No employee selected")
    
    p.save()
    return response


def logout_view(request):
    request.session.flush()  
    return redirect('dashboard')