"""Admin configuration for payroll app."""
from django.contrib import admin
from .models import PayrollPeriod, Paycheck, TaxRate, Deduction, EmployeeDeduction


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ['period_start', 'period_end', 'pay_date', 'status', 'total_gross_pay', 'total_net_pay']
    list_filter = ['status', 'period_start']
    search_fields = ['period_start', 'period_end']
    readonly_fields = ['total_gross_pay', 'total_net_pay', 'created_at', 'updated_at']


@admin.register(Paycheck)
class PaycheckAdmin(admin.ModelAdmin):
    list_display = [
        'employee',
        'payroll_period',
        'gross_pay',
        'total_taxes',
        'total_deductions',
        'net_pay'
    ]
    list_filter = ['payroll_period__status', 'payroll_period__period_start']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    readonly_fields = ['gross_pay', 'net_pay', 'total_taxes', 'total_deductions', 'created_at', 'updated_at']


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ['tax_type', 'state', 'year', 'rate', 'income_min', 'income_max', 'is_active']
    list_filter = ['tax_type', 'year', 'is_active', 'state']
    search_fields = ['tax_type', 'state']


@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = ['name', 'deduction_type', 'default_amount', 'is_percentage', 'frequency', 'is_active']
    list_filter = ['deduction_type', 'frequency', 'is_pre_tax', 'is_active']
    search_fields = ['name', 'description']


@admin.register(EmployeeDeduction)
class EmployeeDeductionAdmin(admin.ModelAdmin):
    list_display = ['employee', 'deduction', 'amount', 'start_date', 'end_date', 'is_active']
    list_filter = ['deduction__deduction_type', 'is_active', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'deduction__name']
