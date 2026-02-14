"""Unit tests for employee models."""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from employees.models import Department, Employee, Address
from datetime import date


@pytest.mark.unit
class TestDepartment:
    """Tests for Department model."""

    def test_create_department(self, db):
        """Test creating a department."""
        dept = Department.objects.create(
            name='Sales',
            code='SALES'
        )
        assert dept.name == 'Sales'
        assert dept.code == 'SALES'
        assert str(dept) == 'SALES - Sales'

    def test_department_unique_code(self, department):
        """Test that department code must be unique."""
        with pytest.raises(IntegrityError):
            Department.objects.create(
                name='Engineering 2',
                code='ENG'  # Duplicate code
            )

    def test_department_unique_name(self, department):
        """Test that department name must be unique."""
        with pytest.raises(IntegrityError):
            Department.objects.create(
                name='Engineering',  # Duplicate name
                code='ENG2'
            )


@pytest.mark.unit
class TestEmployee:
    """Tests for Employee model."""

    def test_create_employee(self, employee):
        """Test creating an employee."""
        assert employee.employee_id == 'EMP001'
        assert employee.first_name == 'John'
        assert employee.last_name == 'Doe'
        assert employee.full_name == 'John Doe'
        assert employee.is_active is True

    def test_employee_unique_id(self, employee):
        """Test that employee ID must be unique."""
        from django.contrib.auth.models import User
        user2 = User.objects.create_user(username='user2')
        with pytest.raises(IntegrityError):
            Employee.objects.create(
                user=user2,
                employee_id='EMP001',  # Duplicate
                first_name='Jane',
                last_name='Smith',
                email='jane@example.com',
                date_of_birth=date(1991, 1, 1),
                ssn_last_four='5678',
                department=employee.department,
                job_title='Engineer',
                employment_type='FULL_TIME',
                hire_date=date(2021, 1, 1),
                base_salary=Decimal('70000.00'),
                pay_frequency='BI_WEEKLY',
            )

    def test_employee_unique_email(self, employee):
        """Test that employee email must be unique."""
        from django.contrib.auth.models import User
        user2 = User.objects.create_user(username='user2')
        with pytest.raises(IntegrityError):
            Employee.objects.create(
                user=user2,
                employee_id='EMP002',
                first_name='Jane',
                last_name='Smith',
                email='john.doe@example.com',  # Duplicate
                date_of_birth=date(1991, 1, 1),
                ssn_last_four='5678',
                department=employee.department,
                job_title='Engineer',
                employment_type='FULL_TIME',
                hire_date=date(2021, 1, 1),
                base_salary=Decimal('70000.00'),
                pay_frequency='BI_WEEKLY',
            )

    def test_calculate_gross_pay_biweekly(self, employee):
        """Test gross pay calculation for bi-weekly employees."""
        gross_pay = employee.calculate_gross_pay()
        expected = Decimal('75000.00') / Decimal('26')
        assert gross_pay == expected.quantize(Decimal('0.01'))

    def test_calculate_gross_pay_weekly(self, employee):
        """Test gross pay calculation for weekly employees."""
        employee.pay_frequency = 'WEEKLY'
        employee.save()
        gross_pay = employee.calculate_gross_pay()
        expected = Decimal('75000.00') / Decimal('52')
        assert gross_pay == expected.quantize(Decimal('0.01'))

    def test_calculate_gross_pay_monthly(self, employee):
        """Test gross pay calculation for monthly employees."""
        employee.pay_frequency = 'MONTHLY'
        employee.save()
        gross_pay = employee.calculate_gross_pay()
        expected = Decimal('75000.00') / Decimal('12')
        assert gross_pay == expected.quantize(Decimal('0.01'))

    def test_calculate_gross_pay_hourly(self, employee):
        """Test gross pay calculation for hourly employees."""
        employee.hourly_rate = Decimal('35.00')
        employee.save()
        gross_pay = employee.calculate_gross_pay(hours_worked=80)
        assert gross_pay == Decimal('2800.00')

    def test_employee_status_active(self, employee):
        """Test active employee status."""
        assert employee.is_active is True

    def test_employee_status_terminated(self, employee):
        """Test terminated employee status."""
        employee.employment_status = 'TERMINATED'
        employee.save()
        assert employee.is_active is False

    def test_base_salary_positive(self, employee):
        """Test that base salary must be positive."""
        employee.base_salary = Decimal('-100.00')
        with pytest.raises(ValidationError):
            employee.full_clean()


@pytest.mark.unit
class TestAddress:
    """Tests for Address model."""

    def test_create_address(self, address):
        """Test creating an address."""
        assert address.street_address_1 == '123 Main St'
        assert address.city == 'Boston'
        assert address.state == 'MA'
        assert address.zip_code == '02101'
        assert address.is_primary is True

    def test_address_unique_type_per_employee(self, employee):
        """Test that each employee can only have one address of each type."""
        Address.objects.create(
            employee=employee,
            address_type='HOME',
            street_address_1='123 Main St',
            city='Boston',
            state='MA',
            zip_code='02101',
        )
        # Attempting to create another HOME address should fail
        with pytest.raises(IntegrityError):
            Address.objects.create(
                employee=employee,
                address_type='HOME',
                street_address_1='456 Oak Ave',
                city='Cambridge',
                state='MA',
                zip_code='02139',
            )

    def test_address_string_representation(self, address):
        """Test address string representation."""
        expected = "John Doe - HOME"
        assert str(address) == expected
