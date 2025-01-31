from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('export_pdf/<int:pk>/', views.export_pdf, name='export_pdf'),
    path('logout/', views.logout_view, name='logout'),
    path('view_records/<int:pk>/', views.EmployeeRecord.as_view(), name='view_records'),  
    path('logout-admin/', views.logout_admin, name='logout_admin'),
    path('export_excel/<int:pk>/', views.export_excel, name='export_excel'),
    path("create-employee/", views.create_employee, name="create_employee"),
    path('view_user_info/<int:employee_id>/', views.view_user_info, name='view_user_info'),

    path('change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),

    path('delete_employee/<int:employee_id>/', views.delete_employee, name='delete_employee'),

]
