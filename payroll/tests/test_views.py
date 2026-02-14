"""Tests for payroll API views."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from payroll.models import PayrollPeriod, Paycheck, TaxRate, Deduction, EmployeeDeduction

User = get_user_model()


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(user):
    """Return authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestPayrollPeriodViewSet:
    """Tests for PayrollPeriod API endpoints."""

    def test_list_payroll_periods(self, authenticated_client, payroll_period):
        """Test listing payroll periods."""
        response = authenticated_client.get('/api/payroll/periods/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_requires_authentication(self, api_client):
        """Test that listing requires authentication."""
        response = api_client.get('/api/payroll/periods/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_payroll_period(self, authenticated_client, payroll_period):
        """Test retrieving a single payroll period."""
        response = authenticated_client.get(f'/api/payroll/periods/{payroll_period.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == payroll_period.id

    def test_create_payroll_period(self, authenticated_client, user):
        """Test creating a payroll period."""
        data = {
            'period_start': '2024-03-01',
            'period_end': '2024-03-15',
            'pay_date': '2024-03-19',
            'status': 'draft',
            'created_by': user.id,
        }
        response = authenticated_client.post('/api/payroll/periods/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'draft'
        assert response.data['period_start'] == '2024-03-01'

    def test_update_payroll_period(self, authenticated_client, payroll_period):
        """Test updating a payroll period."""
        data = {
            'status': 'processing',
        }
        response = authenticated_client.patch(
            f'/api/payroll/periods/{payroll_period.id}/', data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'processing'

    def test_delete_payroll_period(self, authenticated_client, payroll_period):
        """Test deleting a payroll period."""
        response = authenticated_client.delete(
            f'/api/payroll/periods/{payroll_period.id}/'
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_by_status(self, authenticated_client, user):
        """Test filtering payroll periods by status."""
        # Create periods with different statuses
        PayrollPeriod.objects.create(
            period_start=date.today() - timedelta(days=30),
            period_end=date.today() - timedelta(days=16),
            pay_date=date.today() - timedelta(days=12),
            status='draft',
            created_by=user,
        )
        PayrollPeriod.objects.create(
            period_start=date.today() - timedelta(days=15),
            period_end=date.today() - timedelta(days=1),
            pay_date=date.today() + timedelta(days=3),
            status='approved',
            created_by=user,
        )

        response = authenticated_client.get('/api/payroll/periods/?status=draft')

        assert response.status_code == status.HTTP_200_OK
        for period in response.data:
            assert period['status'] == 'draft'

    def test_ordering_by_period_start(self, authenticated_client, user):
        """Test ordering payroll periods by period_start."""
        response = authenticated_client.get('/api/payroll/periods/?ordering=-period_start')

        assert response.status_code == status.HTTP_200_OK

    def test_computed_totals(self, authenticated_client, payroll_period_with_paychecks):
        """Test that computed totals are included."""
        response = authenticated_client.get(
            f'/api/payroll/periods/{payroll_period_with_paychecks.id}/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'total_gross_pay' in response.data
        assert 'total_net_pay' in response.data


@pytest.mark.django_db
class TestPaycheckViewSet:
    """Tests for Paycheck API endpoints."""

    def test_list_paychecks(self, authenticated_client, paycheck):
        """Test listing paychecks."""
        response = authenticated_client.get('/api/payroll/paychecks/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_requires_authentication(self, api_client):
        """Test that listing requires authentication."""
        response = api_client.get('/api/payroll/paychecks/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_paycheck(self, authenticated_client, paycheck):
        """Test retrieving a single paycheck."""
        response = authenticated_client.get(f'/api/payroll/paychecks/{paycheck.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == paycheck.id
        assert 'employee_name' in response.data

    def test_create_paycheck(self, authenticated_client, employee, payroll_period):
        """Test creating a paycheck."""
        data = {
            'employee': employee.id,
            'payroll_period': payroll_period.id,
            'regular_hours': '80.00',
            'overtime_hours': '0.00',
            'regular_pay': '3200.00',
            'overtime_pay': '0.00',
            'bonus': '0.00',
            'commission': '0.00',
            'federal_income_tax': '640.00',
            'state_income_tax': '160.00',
            'social_security_tax': '198.40',
            'medicare_tax': '46.40',
            'health_insurance': '200.00',
            'dental_insurance': '50.00',
            'vision_insurance': '25.00',
            'retirement_contribution': '160.00',
            'other_deductions': '0.00',
        }
        response = authenticated_client.post('/api/payroll/paychecks/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['employee'] == employee.id
        assert Decimal(response.data['regular_hours']) == Decimal('80.00')

    def test_update_paycheck(self, authenticated_client, paycheck):
        """Test updating a paycheck."""
        data = {
            'bonus': '500.00',
        }
        response = authenticated_client.patch(
            f'/api/payroll/paychecks/{paycheck.id}/', data
        )

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['bonus']) == Decimal('500.00')

    def test_delete_paycheck(self, authenticated_client, paycheck):
        """Test deleting a paycheck."""
        response = authenticated_client.delete(f'/api/payroll/paychecks/{paycheck.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_by_employee(self, authenticated_client, employee, paycheck):
        """Test filtering paychecks by employee."""
        response = authenticated_client.get(f'/api/payroll/paychecks/?employee={employee.id}')

        assert response.status_code == status.HTTP_200_OK
        for check in response.data:
            assert check['employee'] == employee.id

    def test_filter_by_payroll_period(self, authenticated_client, payroll_period, paycheck):
        """Test filtering paychecks by payroll period."""
        response = authenticated_client.get(
            f'/api/payroll/paychecks/?payroll_period={payroll_period.id}'
        )

        assert response.status_code == status.HTTP_200_OK
        for check in response.data:
            assert check['payroll_period'] == payroll_period.id

    def test_search_by_employee_name(self, authenticated_client, paycheck):
        """Test searching paychecks by employee name."""
        search_term = paycheck.employee.first_name[:3]
        response = authenticated_client.get(
            f'/api/payroll/paychecks/?search={search_term}'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_search_by_employee_id(self, authenticated_client, paycheck):
        """Test searching paychecks by employee ID."""
        response = authenticated_client.get(
            f'/api/payroll/paychecks/?search={paycheck.employee.employee_id}'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering_by_gross_pay(self, authenticated_client):
        """Test ordering paychecks by gross_pay."""
        response = authenticated_client.get('/api/payroll/paychecks/?ordering=-gross_pay')

        assert response.status_code == status.HTTP_200_OK

    def test_computed_fields(self, authenticated_client, paycheck):
        """Test that computed fields are included."""
        response = authenticated_client.get(f'/api/payroll/paychecks/{paycheck.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert 'total_taxes' in response.data
        assert 'total_deductions' in response.data
        assert 'gross_pay' in response.data
        assert 'net_pay' in response.data


@pytest.mark.django_db
class TestTaxRateViewSet:
    """Tests for TaxRate API endpoints."""

    def test_list_tax_rates(self, authenticated_client):
        """Test listing tax rates."""
        TaxRate.objects.create(
            tax_type='federal',
            year=2024,
            rate=Decimal('0.22'),
            income_min=Decimal('0.00'),
            is_active=True,
        )

        response = authenticated_client.get('/api/payroll/tax-rates/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_tax_rate(self, authenticated_client):
        """Test creating a tax rate."""
        data = {
            'tax_type': 'state',
            'state': 'CA',
            'year': 2024,
            'rate': '0.093',
            'income_min': '0.00',
            'income_max': '100000.00',
            'is_active': True,
        }
        response = authenticated_client.post('/api/payroll/tax-rates/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['tax_type'] == 'state'
        assert response.data['state'] == 'CA'

    def test_filter_by_tax_type(self, authenticated_client):
        """Test filtering tax rates by type."""
        TaxRate.objects.create(
            tax_type='federal',
            year=2024,
            rate=Decimal('0.22'),
            is_active=True,
        )

        response = authenticated_client.get('/api/payroll/tax-rates/?tax_type=federal')

        assert response.status_code == status.HTTP_200_OK
        for rate in response.data:
            assert rate['tax_type'] == 'federal'

    def test_filter_by_year(self, authenticated_client):
        """Test filtering tax rates by year."""
        TaxRate.objects.create(
            tax_type='federal',
            year=2024,
            rate=Decimal('0.22'),
            is_active=True,
        )

        response = authenticated_client.get('/api/payroll/tax-rates/?year=2024')

        assert response.status_code == status.HTTP_200_OK
        for rate in response.data:
            assert rate['year'] == 2024

    def test_filter_by_active_status(self, authenticated_client):
        """Test filtering tax rates by active status."""
        TaxRate.objects.create(
            tax_type='federal',
            year=2024,
            rate=Decimal('0.22'),
            is_active=True,
        )
        TaxRate.objects.create(
            tax_type='federal',
            year=2023,
            rate=Decimal('0.22'),
            is_active=False,
        )

        response = authenticated_client.get('/api/payroll/tax-rates/?is_active=true')

        assert response.status_code == status.HTTP_200_OK
        for rate in response.data:
            assert rate['is_active'] is True


@pytest.mark.django_db
class TestDeductionViewSet:
    """Tests for Deduction API endpoints."""

    def test_list_deductions(self, authenticated_client):
        """Test listing deductions."""
        Deduction.objects.create(
            name='Health Insurance',
            deduction_type='insurance',
            default_amount=Decimal('200.00'),
            is_percentage=False,
            frequency='monthly',
            is_active=True,
        )

        response = authenticated_client.get('/api/payroll/deductions/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_deduction(self, authenticated_client):
        """Test creating a deduction."""
        data = {
            'name': '401(k)',
            'deduction_type': 'retirement',
            'description': 'Retirement savings',
            'default_amount': '5.00',
            'is_percentage': True,
            'frequency': 'per-paycheck',
            'is_pre_tax': True,
            'is_active': True,
        }
        response = authenticated_client.post('/api/payroll/deductions/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == '401(k)'
        assert response.data['is_percentage'] is True

    def test_search_by_name(self, authenticated_client):
        """Test searching deductions by name."""
        Deduction.objects.create(
            name='Health Insurance Premium',
            deduction_type='insurance',
            default_amount=Decimal('200.00'),
            frequency='monthly',
            is_active=True,
        )

        response = authenticated_client.get('/api/payroll/deductions/?search=Health')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_by_type(self, authenticated_client):
        """Test filtering deductions by type."""
        Deduction.objects.create(
            name='Retirement',
            deduction_type='retirement',
            default_amount=Decimal('100.00'),
            frequency='per-paycheck',
            is_active=True,
        )

        response = authenticated_client.get('/api/payroll/deductions/?deduction_type=retirement')

        assert response.status_code == status.HTTP_200_OK
        for deduction in response.data:
            assert deduction['deduction_type'] == 'retirement'

    def test_filter_by_frequency(self, authenticated_client):
        """Test filtering deductions by frequency."""
        Deduction.objects.create(
            name='Monthly Deduction',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            frequency='monthly',
            is_active=True,
        )

        response = authenticated_client.get('/api/payroll/deductions/?frequency=monthly')

        assert response.status_code == status.HTTP_200_OK
        for deduction in response.data:
            assert deduction['frequency'] == 'monthly'


@pytest.mark.django_db
class TestEmployeeDeductionViewSet:
    """Tests for EmployeeDeduction API endpoints."""

    def test_list_employee_deductions(self, authenticated_client, employee):
        """Test listing employee deductions."""
        deduction = Deduction.objects.create(
            name='Test Deduction',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            frequency='per-paycheck',
            is_active=True,
        )
        EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('50.00'),
            is_active=True,
        )

        response = authenticated_client.get('/api/payroll/employee-deductions/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_employee_deduction(self, authenticated_client, employee):
        """Test creating an employee deduction."""
        deduction = Deduction.objects.create(
            name='Custom Deduction',
            deduction_type='other',
            default_amount=Decimal('100.00'),
            frequency='per-paycheck',
            is_active=True,
        )

        data = {
            'employee': employee.id,
            'deduction': deduction.id,
            'amount': '75.00',
            'start_date': '2024-01-01',
            'is_active': True,
        }
        response = authenticated_client.post('/api/payroll/employee-deductions/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['employee'] == employee.id
        assert Decimal(response.data['amount']) == Decimal('75.00')

    def test_filter_by_employee(self, authenticated_client, employee):
        """Test filtering employee deductions by employee."""
        deduction = Deduction.objects.create(
            name='Test',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            frequency='per-paycheck',
            is_active=True,
        )
        EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('50.00'),
            is_active=True,
        )

        response = authenticated_client.get(
            f'/api/payroll/employee-deductions/?employee={employee.id}'
        )

        assert response.status_code == status.HTTP_200_OK
        for emp_deduction in response.data:
            assert emp_deduction['employee'] == employee.id

    def test_search_by_employee_name(self, authenticated_client, employee):
        """Test searching employee deductions by employee name."""
        deduction = Deduction.objects.create(
            name='Search Test',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            frequency='per-paycheck',
            is_active=True,
        )
        EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('50.00'),
            is_active=True,
        )

        search_term = employee.first_name[:3]
        response = authenticated_client.get(
            f'/api/payroll/employee-deductions/?search={search_term}'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_search_by_deduction_name(self, authenticated_client, employee):
        """Test searching employee deductions by deduction name."""
        deduction = Deduction.objects.create(
            name='Searchable Deduction',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            frequency='per-paycheck',
            is_active=True,
        )
        EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('50.00'),
            is_active=True,
        )

        response = authenticated_client.get(
            '/api/payroll/employee-deductions/?search=Searchable'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_employee_name_in_response(self, authenticated_client, employee):
        """Test that employee name is included in response."""
        deduction = Deduction.objects.create(
            name='Test',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            frequency='per-paycheck',
            is_active=True,
        )
        emp_deduction = EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('50.00'),
            is_active=True,
        )

        response = authenticated_client.get(
            f'/api/payroll/employee-deductions/{emp_deduction.id}/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'employee_name' in response.data
        assert response.data['employee_name'] == employee.full_name

    def test_deduction_name_in_response(self, authenticated_client, employee):
        """Test that deduction name is included in response."""
        deduction = Deduction.objects.create(
            name='Named Deduction',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            frequency='per-paycheck',
            is_active=True,
        )
        emp_deduction = EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('50.00'),
            is_active=True,
        )

        response = authenticated_client.get(
            f'/api/payroll/employee-deductions/{emp_deduction.id}/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'deduction_name' in response.data
        assert response.data['deduction_name'] == 'Named Deduction'
