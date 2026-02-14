"""URL configuration for reports app."""
from django.urls import path
from .views import PayrollSummaryReport, SalesSummaryReport, EmployeeSummaryReport

urlpatterns = [
    path('payroll-summary/', PayrollSummaryReport.as_view(), name='payroll-summary'),
    path('sales-summary/', SalesSummaryReport.as_view(), name='sales-summary'),
    path('employee-summary/', EmployeeSummaryReport.as_view(), name='employee-summary'),
]
