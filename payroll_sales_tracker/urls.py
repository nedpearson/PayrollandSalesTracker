"""
URL configuration for payroll_sales_tracker project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/employees/', include('employees.urls')),
    path('api/payroll/', include('payroll.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/reports/', include('reports.urls')),
]
