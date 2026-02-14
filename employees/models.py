"""Employee models for the payroll and sales tracker."""
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, EmailValidator


class Department(models.Model):
    """Department model."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Employee(models.Model):
    """Employee model with comprehensive payroll information."""

    EMPLOYMENT_STATUS = [
        ('ACTIVE', 'Active'),
        ('ON_LEAVE', 'On Leave'),
        ('TERMINATED', 'Terminated'),
        ('SUSPENDED', 'Suspended'),
    ]

    EMPLOYMENT_TYPE = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
    ]

    PAY_FREQUENCY = [
        ('WEEKLY', 'Weekly'),
        ('BI_WEEKLY', 'Bi-Weekly'),
        ('SEMI_MONTHLY', 'Semi-Monthly'),
        ('MONTHLY', 'Monthly'),
    ]

    # Personal Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField()
    ssn_last_four = models.CharField(max_length=4, help_text="Last 4 digits of SSN")

    # Employment Information
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees'
    )
    job_title = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE)
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default='ACTIVE'
    )
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)

    # Compensation
    base_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    pay_frequency = models.CharField(max_length=20, choices=PAY_FREQUENCY)
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Tax Information
    tax_filing_status = models.CharField(max_length=20, default='SINGLE')
    federal_allowances = models.IntegerField(default=0)
    state_allowances = models.IntegerField(default=0)
    additional_withholding = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Benefits
    has_health_insurance = models.BooleanField(default=False)
    has_dental_insurance = models.BooleanField(default=False)
    has_vision_insurance = models.BooleanField(default=False)
    retirement_contribution_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['employment_status']),
            models.Index(fields=['department', 'employment_status']),
        ]

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """Return full name of employee."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self):
        """Check if employee is active."""
        return self.employment_status == 'ACTIVE'

    def calculate_gross_pay(self, hours_worked=None):
        """Calculate gross pay based on employment type and hours."""
        if self.employment_type in ['FULL_TIME', 'PART_TIME'] and self.pay_frequency:
            if self.pay_frequency == 'WEEKLY':
                return self.base_salary / Decimal('52')
            elif self.pay_frequency == 'BI_WEEKLY':
                return self.base_salary / Decimal('26')
            elif self.pay_frequency == 'SEMI_MONTHLY':
                return self.base_salary / Decimal('24')
            elif self.pay_frequency == 'MONTHLY':
                return self.base_salary / Decimal('12')
        elif self.hourly_rate and hours_worked:
            return self.hourly_rate * Decimal(str(hours_worked))
        return Decimal('0.00')


class Address(models.Model):
    """Employee address model."""

    ADDRESS_TYPE = [
        ('HOME', 'Home'),
        ('MAILING', 'Mailing'),
        ('WORK', 'Work'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE)
    street_address_1 = models.CharField(max_length=255)
    street_address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='USA')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Addresses'
        unique_together = ['employee', 'address_type']

    def __str__(self):
        return f"{self.employee.full_name} - {self.address_type}"
