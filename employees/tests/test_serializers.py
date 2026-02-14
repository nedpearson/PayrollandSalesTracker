"""Tests for employees serializers."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from employees.models import Department, Employee, Address
from employees.serializers import DepartmentSerializer, EmployeeSerializer, AddressSerializer

User = get_user_model()


@pytest.mark.django_db
class TestDepartmentSerializer:
    """Tests for DepartmentSerializer."""

    def test_serialization(self, department):
        """Test department serialization."""
        serializer = DepartmentSerializer(department)
        data = serializer.data

        assert data['id'] == department.id
        assert data['name'] == department.name
        assert data['code'] == department.code
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_deserialization(self):
        """Test department deserialization."""
        data = {
            'name': 'Engineering',
            'code': 'ENG',
        }
        serializer = DepartmentSerializer(data=data)

        assert serializer.is_valid()
        department = serializer.save()

        assert department.name == 'Engineering'
        assert department.code == 'ENG'

    def test_unique_code_validation(self, department):
        """Test unique code constraint validation."""
        data = {
            'name': 'Another Dept',
            'code': department.code,  # Duplicate code
        }
        serializer = DepartmentSerializer(data=data)

        assert not serializer.is_valid()
        assert 'code' in serializer.errors

    def test_read_only_fields(self, department):
        """Test that read-only fields cannot be updated."""
        original_created_at = department.created_at
        data = {
            'name': 'Updated Name',
            'code': department.code,
            'created_at': date.today(),  # Try to update read-only field
        }
        serializer = DepartmentSerializer(department, data=data, partial=True)

        assert serializer.is_valid()
        serializer.save()

        department.refresh_from_db()
        assert department.created_at == original_created_at  # Should not change

    def test_optional_manager_field(self):
        """Test department creation without manager."""
        data = {
            'name': 'HR',
            'code': 'HR',
        }
        serializer = DepartmentSerializer(data=data)

        assert serializer.is_valid()
        department = serializer.save()
        assert department.manager is None


@pytest.mark.django_db
class TestAddressSerializer:
    """Tests for AddressSerializer."""

    def test_serialization(self, employee_with_address):
        """Test address serialization."""
        address = employee_with_address.addresses.first()
        serializer = AddressSerializer(address)
        data = serializer.data

        assert data['id'] == address.id
        assert data['employee'] == employee_with_address.id
        assert data['address_type'] == address.address_type
        assert data['street_address_1'] == address.street_address_1
        assert data['city'] == address.city
        assert data['state'] == address.state
        assert data['zip_code'] == address.zip_code

    def test_deserialization(self, employee):
        """Test address deserialization."""
        data = {
            'employee': employee.id,
            'address_type': 'home',
            'street_address_1': '456 Oak St',
            'city': 'Portland',
            'state': 'OR',
            'zip_code': '97201',
            'country': 'USA',
            'is_primary': True,
        }
        serializer = AddressSerializer(data=data)

        assert serializer.is_valid()
        address = serializer.save()

        assert address.employee == employee
        assert address.city == 'Portland'
        assert address.is_primary is True

    def test_optional_fields(self, employee):
        """Test address creation with only required fields."""
        data = {
            'employee': employee.id,
            'address_type': 'home',
            'street_address_1': '123 Main St',
            'city': 'Seattle',
            'state': 'WA',
            'zip_code': '98101',
        }
        serializer = AddressSerializer(data=data)

        assert serializer.is_valid()
        address = serializer.save()
        assert address.street_address_2 is None or address.street_address_2 == ''
        assert address.country == 'USA'  # Default value

    def test_multiple_addresses_for_employee(self, employee):
        """Test creating multiple addresses for same employee."""
        address1_data = {
            'employee': employee.id,
            'address_type': 'home',
            'street_address_1': '123 Home St',
            'city': 'Seattle',
            'state': 'WA',
            'zip_code': '98101',
            'is_primary': True,
        }
        address2_data = {
            'employee': employee.id,
            'address_type': 'work',
            'street_address_1': '456 Work Ave',
            'city': 'Bellevue',
            'state': 'WA',
            'zip_code': '98004',
            'is_primary': False,
        }

        serializer1 = AddressSerializer(data=address1_data)
        serializer2 = AddressSerializer(data=address2_data)

        assert serializer1.is_valid()
        assert serializer2.is_valid()

        address1 = serializer1.save()
        address2 = serializer2.save()

        assert employee.addresses.count() == 2
        assert address1.is_primary is True
        assert address2.is_primary is False


@pytest.mark.django_db
class TestEmployeeSerializer:
    """Tests for EmployeeSerializer."""

    def test_serialization(self, employee):
        """Test employee serialization."""
        serializer = EmployeeSerializer(employee)
        data = serializer.data

        assert data['id'] == employee.id
        assert data['employee_id'] == employee.employee_id
        assert data['first_name'] == employee.first_name
        assert data['last_name'] == employee.last_name
        assert data['full_name'] == employee.full_name
        assert data['email'] == employee.email
        assert data['is_active'] == employee.is_active
        assert 'addresses' in data

    def test_full_name_read_only(self, employee):
        """Test that full_name is read-only and computed."""
        serializer = EmployeeSerializer(employee)
        data = serializer.data

        expected_full_name = f"{employee.first_name} {employee.last_name}"
        assert data['full_name'] == expected_full_name

    def test_is_active_read_only(self, employee):
        """Test that is_active is read-only and computed."""
        serializer = EmployeeSerializer(employee)
        data = serializer.data

        assert data['is_active'] is True
        assert employee.termination_date is None

    def test_deserialization(self, department):
        """Test employee deserialization."""
        data = {
            'employee_id': 'EMP999',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@example.com',
            'phone': '555-0102',
            'date_of_birth': '1990-01-15',
            'department': department.id,
            'job_title': 'Software Engineer',
            'employment_type': 'full-time',
            'employment_status': 'active',
            'hire_date': '2024-01-01',
            'base_salary': '80000.00',
            'pay_frequency': 'bi-weekly',
        }
        serializer = EmployeeSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        employee = serializer.save()

        assert employee.first_name == 'Jane'
        assert employee.last_name == 'Doe'
        assert employee.employee_id == 'EMP999'
        assert employee.email == 'jane.doe@example.com'
        assert employee.base_salary == Decimal('80000.00')

    def test_unique_employee_id_validation(self, employee):
        """Test unique employee_id constraint validation."""
        data = {
            'employee_id': employee.employee_id,  # Duplicate
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'department': employee.department.id,
            'job_title': 'Tester',
            'employment_type': 'full-time',
            'employment_status': 'active',
            'hire_date': '2024-01-01',
        }
        serializer = EmployeeSerializer(data=data)

        assert not serializer.is_valid()
        assert 'employee_id' in serializer.errors

    def test_unique_email_validation(self, employee):
        """Test unique email constraint validation."""
        data = {
            'employee_id': 'EMP888',
            'first_name': 'Test',
            'last_name': 'User',
            'email': employee.email,  # Duplicate
            'department': employee.department.id,
            'job_title': 'Tester',
            'employment_type': 'full-time',
            'employment_status': 'active',
            'hire_date': '2024-01-01',
        }
        serializer = EmployeeSerializer(data=data)

        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_nested_addresses_serialization(self, employee_with_address):
        """Test nested addresses serialization."""
        serializer = EmployeeSerializer(employee_with_address)
        data = serializer.data

        assert 'addresses' in data
        assert isinstance(data['addresses'], list)
        assert len(data['addresses']) == 1

        address = data['addresses'][0]
        assert 'street_address_1' in address
        assert 'city' in address
        assert 'state' in address

    def test_addresses_read_only(self, employee, department):
        """Test that nested addresses are read-only."""
        address_data = {
            'address_type': 'home',
            'street_address_1': '789 Elm St',
            'city': 'Portland',
            'state': 'OR',
            'zip_code': '97201',
        }
        data = {
            'employee_id': 'EMP777',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test777@example.com',
            'department': department.id,
            'job_title': 'Tester',
            'employment_type': 'full-time',
            'employment_status': 'active',
            'hire_date': '2024-01-01',
            'addresses': [address_data],  # Try to create nested address
        }
        serializer = EmployeeSerializer(data=data)

        assert serializer.is_valid()
        employee = serializer.save()

        # Addresses should not be created via nested data
        assert employee.addresses.count() == 0

    def test_hourly_employee(self, department):
        """Test creating hourly employee."""
        data = {
            'employee_id': 'EMP666',
            'first_name': 'Hourly',
            'last_name': 'Worker',
            'email': 'hourly@example.com',
            'department': department.id,
            'job_title': 'Contractor',
            'employment_type': 'part-time',
            'employment_status': 'active',
            'hire_date': '2024-01-01',
            'pay_frequency': 'hourly',
            'hourly_rate': '25.50',
        }
        serializer = EmployeeSerializer(data=data)

        assert serializer.is_valid()
        employee = serializer.save()

        assert employee.hourly_rate == Decimal('25.50')
        assert employee.base_salary == Decimal('0.00')

    def test_terminated_employee(self, employee):
        """Test updating employee with termination date."""
        data = {
            'employment_status': 'terminated',
            'termination_date': date.today(),
        }
        serializer = EmployeeSerializer(employee, data=data, partial=True)

        assert serializer.is_valid()
        updated_employee = serializer.save()

        assert updated_employee.employment_status == 'terminated'
        assert updated_employee.termination_date == date.today()

    def test_tax_withholding_fields(self, department):
        """Test tax withholding fields."""
        data = {
            'employee_id': 'EMP555',
            'first_name': 'Tax',
            'last_name': 'Payer',
            'email': 'taxpayer@example.com',
            'department': department.id,
            'job_title': 'Accountant',
            'employment_type': 'full-time',
            'employment_status': 'active',
            'hire_date': '2024-01-01',
            'base_salary': '70000.00',
            'pay_frequency': 'bi-weekly',
            'tax_filing_status': 'married',
            'federal_allowances': 2,
            'state_allowances': 2,
            'additional_withholding': '100.00',
        }
        serializer = EmployeeSerializer(data=data)

        assert serializer.is_valid()
        employee = serializer.save()

        assert employee.tax_filing_status == 'married'
        assert employee.federal_allowances == 2
        assert employee.state_allowances == 2
        assert employee.additional_withholding == Decimal('100.00')

    def test_benefits_fields(self, department):
        """Test employee benefits fields."""
        data = {
            'employee_id': 'EMP444',
            'first_name': 'Benefits',
            'last_name': 'User',
            'email': 'benefits@example.com',
            'department': department.id,
            'job_title': 'Manager',
            'employment_type': 'full-time',
            'employment_status': 'active',
            'hire_date': '2024-01-01',
            'base_salary': '90000.00',
            'pay_frequency': 'bi-weekly',
            'has_health_insurance': True,
            'has_dental_insurance': True,
            'has_vision_insurance': False,
            'retirement_contribution_percent': '5.00',
        }
        serializer = EmployeeSerializer(data=data)

        assert serializer.is_valid()
        employee = serializer.save()

        assert employee.has_health_insurance is True
        assert employee.has_dental_insurance is True
        assert employee.has_vision_insurance is False
        assert employee.retirement_contribution_percent == Decimal('5.00')

    def test_partial_update(self, employee):
        """Test partial update of employee."""
        original_email = employee.email
        data = {
            'phone': '555-9999',
        }
        serializer = EmployeeSerializer(employee, data=data, partial=True)

        assert serializer.is_valid()
        updated_employee = serializer.save()

        assert updated_employee.phone == '555-9999'
        assert updated_employee.email == original_email  # Should remain unchanged

    def test_ssn_last_four_field(self, department):
        """Test SSN last four digits field."""
        data = {
            'employee_id': 'EMP333',
            'first_name': 'Secure',
            'last_name': 'Employee',
            'email': 'secure@example.com',
            'department': department.id,
            'job_title': 'Analyst',
            'employment_type': 'full-time',
            'employment_status': 'active',
            'hire_date': '2024-01-01',
            'base_salary': '65000.00',
            'pay_frequency': 'bi-weekly',
            'ssn_last_four': '1234',
        }
        serializer = EmployeeSerializer(data=data)

        assert serializer.is_valid()
        employee = serializer.save()

        assert employee.ssn_last_four == '1234'
