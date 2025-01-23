from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('logout/', views.logout_view, name='logout'),
]
