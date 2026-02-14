"""Payroll models for payroll processing and tax calculations."""
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from employees.models import Employee


class PayrollPeriod(models.Model):
    """Payroll period model."""

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PROCESSING', 'Processing'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid'),
        ('CLOSED', 'Closed'),
    ]

    period_start = models.DateField()
    period_end = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='created_payroll_periods'
    )
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payroll_periods'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_start']
        unique_together = ['period_start', 'period_end']

    def __str__(self):
        return f"Payroll {self.period_start} to {self.period_end}"

    @property
    def total_gross_pay(self):
        """Calculate total gross pay for this period."""
        return sum(
            paycheck.gross_pay for paycheck in self.paychecks.all()
        ) or Decimal('0.00')

    @property
    def total_net_pay(self):
        """Calculate total net pay for this period."""
        return sum(
            paycheck.net_pay for paycheck in self.paychecks.all()
        ) or Decimal('0.00')


class Paycheck(models.Model):
    """Individual employee paycheck."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='paychecks'
    )
    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name='paychecks'
    )

    # Hours and earnings
    regular_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    overtime_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    regular_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    overtime_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    bonus = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    commission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Calculated amounts
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)

    # Taxes
    federal_income_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    state_income_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    social_security_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    medicare_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Deductions
    health_insurance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    dental_insurance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    vision_insurance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    retirement_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    other_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Net pay
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payroll_period__period_start', 'employee__last_name']
        unique_together = ['employee', 'payroll_period']
        indexes = [
            models.Index(fields=['employee', 'payroll_period']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_period}"

    @property
    def total_taxes(self):
        """Calculate total tax withholdings."""
        return (
            self.federal_income_tax +
            self.state_income_tax +
            self.social_security_tax +
            self.medicare_tax
        )

    @property
    def total_deductions(self):
        """Calculate total deductions (excluding taxes)."""
        return (
            self.health_insurance +
            self.dental_insurance +
            self.vision_insurance +
            self.retirement_contribution +
            self.other_deductions
        )

    def calculate_gross_pay(self):
        """Calculate gross pay from components."""
        return (
            self.regular_pay +
            self.overtime_pay +
            self.bonus +
            self.commission
        )

    def calculate_net_pay(self):
        """Calculate net pay after taxes and deductions."""
        return self.gross_pay - self.total_taxes - self.total_deductions

    def save(self, *args, **kwargs):
        """Override save to calculate gross and net pay."""
        self.gross_pay = self.calculate_gross_pay()
        self.net_pay = self.calculate_net_pay()
        super().save(*args, **kwargs)


class TaxRate(models.Model):
    """Tax rate configuration."""

    TAX_TYPE_CHOICES = [
        ('FEDERAL_INCOME', 'Federal Income Tax'),
        ('STATE_INCOME', 'State Income Tax'),
        ('SOCIAL_SECURITY', 'Social Security'),
        ('MEDICARE', 'Medicare'),
        ('LOCAL', 'Local Tax'),
    ]

    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES)
    state = models.CharField(max_length=2, blank=True, help_text="State code for state taxes")
    year = models.IntegerField()
    rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0000'))]
    )
    income_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    income_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank for unlimited"
    )
    additional_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Additional flat amount to add"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tax_type', 'year', 'income_min']
        indexes = [
            models.Index(fields=['tax_type', 'year', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_tax_type_display()} - {self.year} ({self.rate}%)"


class Deduction(models.Model):
    """Pre-configured deduction types."""

    DEDUCTION_TYPE_CHOICES = [
        ('HEALTH', 'Health Insurance'),
        ('DENTAL', 'Dental Insurance'),
        ('VISION', 'Vision Insurance'),
        ('RETIREMENT', 'Retirement Contribution'),
        ('HSA', 'Health Savings Account'),
        ('FSA', 'Flexible Spending Account'),
        ('LIFE', 'Life Insurance'),
        ('DISABILITY', 'Disability Insurance'),
        ('GARNISHMENT', 'Wage Garnishment'),
        ('OTHER', 'Other'),
    ]

    FREQUENCY_CHOICES = [
        ('PER_PAYCHECK', 'Per Paycheck'),
        ('MONTHLY', 'Monthly'),
        ('ANNUAL', 'Annual'),
    ]

    name = models.CharField(max_length=100)
    deduction_type = models.CharField(max_length=20, choices=DEDUCTION_TYPE_CHOICES)
    description = models.TextField(blank=True)
    default_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    is_percentage = models.BooleanField(
        default=False,
        help_text="If true, default_amount is a percentage of gross pay"
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_pre_tax = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_deduction_type_display()})"


class EmployeeDeduction(models.Model):
    """Employee-specific deduction configuration."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='deductions'
    )
    deduction = models.ForeignKey(
        Deduction,
        on_delete=models.PROTECT,
        related_name='employee_deductions'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount or percentage based on deduction configuration"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee', 'deduction']
        unique_together = ['employee', 'deduction']

    def __str__(self):
        return f"{self.employee.full_name} - {self.deduction.name}"
