from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('logout/', views.logout_view, name='logout'),
    path('view_records/<int:pk>/', views.EmployeeRecord.as_view(), name='view_records'),  
]
