"""Fixtures for employee tests."""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from employees.models import Department, Employee, Address
from datetime import date


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def department(db):
    """Create a test department."""
    return Department.objects.create(
        name='Engineering',
        code='ENG'
    )


@pytest.fixture
def employee(db, user, department):
    """Create a test employee."""
    return Employee.objects.create(
        user=user,
        employee_id='EMP001',
        first_name='John',
        last_name='Doe',
        email='john.doe@example.com',
        phone='555-1234',
        date_of_birth=date(1990, 1, 1),
        ssn_last_four='1234',
        department=department,
        job_title='Software Engineer',
        employment_type='FULL_TIME',
        employment_status='ACTIVE',
        hire_date=date(2020, 1, 1),
        base_salary=Decimal('75000.00'),
        pay_frequency='BI_WEEKLY',
        tax_filing_status='SINGLE',
        federal_allowances=1,
        state_allowances=1,
    )


@pytest.fixture
def address(db, employee):
    """Create a test address."""
    return Address.objects.create(
        employee=employee,
        address_type='HOME',
        street_address_1='123 Main St',
        city='Boston',
        state='MA',
        zip_code='02101',
        is_primary=True
    )
