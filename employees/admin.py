"""Admin configuration for employees app."""
from django.contrib import admin
from .models import Department, Employee, Address


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'manager', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']


class AddressInline(admin.TabularInline):
    model = Address
    extra = 1


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id',
        'full_name',
        'department',
        'job_title',
        'employment_status',
        'hire_date'
    ]
    list_filter = ['employment_status', 'employment_type', 'department', 'pay_frequency']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AddressInline]
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'employee_id', 'first_name', 'last_name', 'email', 'phone',
                      'date_of_birth', 'ssn_last_four')
        }),
        ('Employment Information', {
            'fields': ('department', 'job_title', 'employment_type', 'employment_status',
                      'hire_date', 'termination_date')
        }),
        ('Compensation', {
            'fields': ('base_salary', 'pay_frequency', 'hourly_rate')
        }),
        ('Tax Information', {
            'fields': ('tax_filing_status', 'federal_allowances', 'state_allowances',
                      'additional_withholding')
        }),
        ('Benefits', {
            'fields': ('has_health_insurance', 'has_dental_insurance', 'has_vision_insurance',
                      'retirement_contribution_percent')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['employee', 'address_type', 'city', 'state', 'is_primary']
    list_filter = ['address_type', 'state', 'is_primary']
    search_fields = ['employee__first_name', 'employee__last_name', 'city', 'state']
