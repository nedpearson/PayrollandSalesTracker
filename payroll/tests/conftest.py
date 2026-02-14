"""Fixtures for payroll tests."""
import pytest
from decimal import Decimal
from datetime import date
from django.contrib.auth.models import User
from employees.models import Department, Employee
from payroll.models import (
    PayrollPeriod, Paycheck, TaxRate, Deduction, EmployeeDeduction
)


@pytest.fixture
def payroll_user(db):
    """Create a payroll user."""
    return User.objects.create_user(
        username='payroll_admin',
        email='payroll@example.com',
        password='payrollpass123'
    )


@pytest.fixture
def payroll_department(db):
    """Create a department for payroll testing."""
    return Department.objects.create(
        name='Sales',
        code='SALES'
    )


@pytest.fixture
def payroll_employee(db, payroll_department):
    """Create an employee for payroll testing."""
    user = User.objects.create_user(username='emp_payroll')
    return Employee.objects.create(
        user=user,
        employee_id='EMP100',
        first_name='Alice',
        last_name='Johnson',
        email='alice@example.com',
        date_of_birth=date(1985, 5, 15),
        ssn_last_four='5678',
        department=payroll_department,
        job_title='Sales Representative',
        employment_type='FULL_TIME',
        employment_status='ACTIVE',
        hire_date=date(2019, 1, 1),
        base_salary=Decimal('60000.00'),
        pay_frequency='BI_WEEKLY',
        tax_filing_status='SINGLE',
        federal_allowances=1,
        state_allowances=1,
        has_health_insurance=True,
        retirement_contribution_percent=Decimal('5.00'),
    )


@pytest.fixture
def payroll_period(db, payroll_user):
    """Create a payroll period."""
    return PayrollPeriod.objects.create(
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 15),
        pay_date=date(2024, 1, 19),
        status='DRAFT',
        created_by=payroll_user,
    )


@pytest.fixture
def paycheck(db, payroll_employee, payroll_period):
    """Create a paycheck."""
    return Paycheck.objects.create(
        employee=payroll_employee,
        payroll_period=payroll_period,
        regular_hours=Decimal('80.00'),
        regular_pay=Decimal('2307.69'),
        overtime_hours=Decimal('0.00'),
        overtime_pay=Decimal('0.00'),
        bonus=Decimal('0.00'),
        commission=Decimal('500.00'),
        federal_income_tax=Decimal('280.77'),
        state_income_tax=Decimal('140.38'),
        social_security_tax=Decimal('174.08'),
        medicare_tax=Decimal('40.71'),
        health_insurance=Decimal('100.00'),
        retirement_contribution=Decimal('115.38'),
    )


@pytest.fixture
def federal_tax_rate(db):
    """Create a federal tax rate."""
    return TaxRate.objects.create(
        tax_type='FEDERAL_INCOME',
        year=2024,
        rate=Decimal('12.0000'),
        income_min=Decimal('10275.00'),
        income_max=Decimal('41775.00'),
        is_active=True,
    )


@pytest.fixture
def health_deduction(db):
    """Create a health insurance deduction."""
    return Deduction.objects.create(
        name='Health Insurance',
        deduction_type='HEALTH',
        description='Employee health insurance premium',
        default_amount=Decimal('100.00'),
        is_percentage=False,
        frequency='PER_PAYCHECK',
        is_pre_tax=True,
        is_active=True,
    )
