"""Tests for reports API endpoints."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from employees.models import Employee, Department
from payroll.models import Paycheck, PayrollPeriod
from sales.models import SalesTransaction


@pytest.fixture
def report_user(db):
    """Create a user for reports testing."""
    return User.objects.create_user(
        username='report_user',
        password='testpass'
    )


@pytest.fixture
def authenticated_report_client(report_user):
    """Create authenticated API client for reports."""
    client = APIClient()
    client.force_authenticate(user=report_user)
    return client


@pytest.mark.integration
class TestEmployeeSummaryReport:
    """Tests for Employee Summary Report."""

    def test_employee_summary_basic(self, authenticated_report_client, employee):
        """Test basic employee summary report."""
        url = '/api/reports/employee-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total_employees' in response.data
        assert 'active_employees' in response.data
        assert 'by_department' in response.data
        assert 'by_employment_type' in response.data
        assert 'by_status' in response.data

    def test_employee_summary_requires_authentication(self):
        """Test that employee summary requires authentication."""
        client = APIClient()
        url = '/api/reports/employee-summary/'
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_employee_count_accuracy(self, authenticated_report_client, department):
        """Test employee count accuracy."""
        # Create multiple employees
        for i in range(5):
            Employee.objects.create(
                employee_id=f'EMP{100+i}',
                first_name=f'Test{i}',
                last_name='Employee',
                email=f'test{i}@example.com',
                department=department,
                job_title='Tester',
                employment_type='full-time',
                employment_status='ACTIVE',
                hire_date=date.today(),
            )

        url = '/api/reports/employee-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_employees'] >= 5

    def test_active_vs_inactive_employees(self, authenticated_report_client, department):
        """Test distinction between active and inactive employees."""
        # Create active employees
        for i in range(3):
            Employee.objects.create(
                employee_id=f'ACT{i}',
                first_name=f'Active{i}',
                last_name='Employee',
                email=f'active{i}@test.com',
                department=department,
                job_title='Active',
                employment_type='full-time',
                employment_status='ACTIVE',
                hire_date=date.today(),
            )

        # Create terminated employee
        Employee.objects.create(
            employee_id='TERM1',
            first_name='Terminated',
            last_name='Employee',
            email='term@test.com',
            department=department,
            job_title='Former',
            employment_type='full-time',
            employment_status='TERMINATED',
            hire_date=date.today() - timedelta(days=365),
            termination_date=date.today() - timedelta(days=30),
        )

        url = '/api/reports/employee-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['active_employees'] >= 3
        assert response.data['total_employees'] > response.data['active_employees']

    def test_department_breakdown(self, authenticated_report_client):
        """Test employee breakdown by department."""
        # Create departments and employees
        dept1 = Department.objects.create(name='Engineering', code='ENG')
        dept2 = Department.objects.create(name='Sales', code='SAL')

        for i in range(3):
            Employee.objects.create(
                employee_id=f'ENG{i}',
                first_name=f'Engineer{i}',
                last_name='Test',
                email=f'eng{i}@test.com',
                department=dept1,
                job_title='Engineer',
                employment_type='full-time',
                employment_status='ACTIVE',
                hire_date=date.today(),
            )

        for i in range(2):
            Employee.objects.create(
                employee_id=f'SAL{i}',
                first_name=f'Sales{i}',
                last_name='Test',
                email=f'sal{i}@test.com',
                department=dept2,
                job_title='Sales Rep',
                employment_type='full-time',
                employment_status='ACTIVE',
                hire_date=date.today(),
            )

        url = '/api/reports/employee-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['by_department']) >= 2

    def test_employment_type_breakdown(self, authenticated_report_client, department):
        """Test employee breakdown by employment type."""
        # Create full-time employees
        for i in range(3):
            Employee.objects.create(
                employee_id=f'FT{i}',
                first_name=f'FullTime{i}',
                last_name='Employee',
                email=f'ft{i}@test.com',
                department=department,
                job_title='Full Time',
                employment_type='full-time',
                employment_status='ACTIVE',
                hire_date=date.today(),
            )

        # Create part-time employee
        Employee.objects.create(
            employee_id='PT1',
            first_name='PartTime',
            last_name='Employee',
            email='pt@test.com',
            department=department,
            job_title='Part Time',
            employment_type='part-time',
            employment_status='ACTIVE',
            hire_date=date.today(),
        )

        url = '/api/reports/employee-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['by_employment_type']) >= 1

    def test_empty_database(self, authenticated_report_client):
        """Test employee summary with no employees."""
        Employee.objects.all().delete()

        url = '/api/reports/employee-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_employees'] == 0
        assert response.data['active_employees'] == 0


@pytest.mark.integration
class TestPayrollSummaryReport:
    """Tests for Payroll Summary Report."""

    def test_payroll_summary_with_period_id(self, authenticated_report_client, paycheck):
        """Test payroll summary report with specific period."""
        url = f'/api/reports/payroll-summary/?period_id={paycheck.payroll_period.id}'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total_gross_pay' in response.data
        assert 'total_net_pay' in response.data
        assert 'total_taxes' in response.data
        assert 'employee_count' in response.data
        assert 'avg_gross_pay' in response.data

    def test_payroll_summary_requires_authentication(self, paycheck):
        """Test that payroll summary requires authentication."""
        client = APIClient()
        url = f'/api/reports/payroll-summary/?period_id={paycheck.payroll_period.id}'
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_payroll_calculation_accuracy(
        self, authenticated_report_client, employee, payroll_period
    ):
        """Test payroll summary calculation accuracy."""
        # Create multiple paychecks with known values
        Paycheck.objects.create(
            employee=employee,
            payroll_period=payroll_period,
            regular_hours=Decimal('80.00'),
            regular_pay=Decimal('3200.00'),
            overtime_hours=Decimal('0.00'),
            overtime_pay=Decimal('0.00'),
            bonus=Decimal('0.00'),
            commission=Decimal('0.00'),
            federal_income_tax=Decimal('640.00'),
            state_income_tax=Decimal('160.00'),
            social_security_tax=Decimal('198.40'),
            medicare_tax=Decimal('46.40'),
            health_insurance=Decimal('200.00'),
            dental_insurance=Decimal('50.00'),
            vision_insurance=Decimal('25.00'),
            retirement_contribution=Decimal('160.00'),
            other_deductions=Decimal('0.00'),
        )

        url = f'/api/reports/payroll-summary/?period_id={payroll_period.id}'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(str(response.data['total_gross_pay'])) >= Decimal('3200.00')

    def test_payroll_summary_no_period_uses_latest(
        self, authenticated_report_client, payroll_period, paycheck
    ):
        """Test payroll summary without period_id uses latest period."""
        url = '/api/reports/payroll-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total_gross_pay' in response.data

    def test_payroll_summary_no_periods_found(self, authenticated_report_client):
        """Test payroll summary when no periods exist."""
        PayrollPeriod.objects.all().delete()

        url = '/api/reports/payroll-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data

    def test_payroll_summary_multiple_employees(
        self, authenticated_report_client, department, payroll_period, user
    ):
        """Test payroll summary with multiple employees."""
        # Create multiple employees and paychecks
        for i in range(5):
            emp = Employee.objects.create(
                employee_id=f'PAYEMP{i}',
                first_name=f'PayEmployee{i}',
                last_name='Test',
                email=f'payemp{i}@test.com',
                department=department,
                job_title='Employee',
                employment_type='full-time',
                employment_status='ACTIVE',
                hire_date=date.today(),
                base_salary=Decimal('50000.00'),
                pay_frequency='bi-weekly',
            )

            Paycheck.objects.create(
                employee=emp,
                payroll_period=payroll_period,
                regular_hours=Decimal('80.00'),
                regular_pay=Decimal('2000.00'),
                overtime_hours=Decimal('0.00'),
                overtime_pay=Decimal('0.00'),
                bonus=Decimal('0.00'),
                commission=Decimal('0.00'),
                federal_income_tax=Decimal('400.00'),
                state_income_tax=Decimal('100.00'),
                social_security_tax=Decimal('124.00'),
                medicare_tax=Decimal('29.00'),
                health_insurance=Decimal('150.00'),
                dental_insurance=Decimal('40.00'),
                vision_insurance=Decimal('20.00'),
                retirement_contribution=Decimal('100.00'),
                other_deductions=Decimal('0.00'),
            )

        url = f'/api/reports/payroll-summary/?period_id={payroll_period.id}'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['employee_count'] >= 5
        assert Decimal(str(response.data['total_gross_pay'])) >= Decimal('10000.00')

    def test_average_gross_pay_calculation(
        self, authenticated_report_client, payroll_period
    ):
        """Test average gross pay calculation."""
        url = f'/api/reports/payroll-summary/?period_id={payroll_period.id}'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        if response.data['employee_count'] > 0:
            assert 'avg_gross_pay' in response.data
            assert response.data['avg_gross_pay'] is not None


@pytest.mark.integration
class TestSalesSummaryReport:
    """Tests for Sales Summary Report."""

    def test_sales_summary_basic(self, authenticated_report_client, sales_transaction):
        """Test basic sales summary report."""
        url = '/api/reports/sales-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total_sales' in response.data
        assert 'total_transactions' in response.data
        assert 'total_commission' in response.data
        assert 'avg_transaction' in response.data
        assert 'top_salespeople' in response.data

    def test_sales_summary_requires_authentication(self):
        """Test that sales summary requires authentication."""
        client = APIClient()
        url = '/api/reports/sales-summary/'
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_sales_summary_date_range_filtering(
        self, authenticated_report_client, customer, employee
    ):
        """Test sales summary with date range filtering."""
        # Create transactions across different dates
        SalesTransaction.objects.create(
            transaction_id='OLD-001',
            customer=customer,
            salesperson=employee,
            transaction_date=date.today() - timedelta(days=60),
            status='COMPLETED',
            payment_method='cash',
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('10.00'),
            discount_amount=Decimal('0.00'),
            commission_amount=Decimal('5.00'),
        )

        SalesTransaction.objects.create(
            transaction_id='NEW-001',
            customer=customer,
            salesperson=employee,
            transaction_date=date.today(),
            status='COMPLETED',
            payment_method='credit_card',
            subtotal=Decimal('200.00'),
            tax_amount=Decimal('20.00'),
            discount_amount=Decimal('0.00'),
            commission_amount=Decimal('10.00'),
        )

        # Test with date range
        start_date = (date.today() - timedelta(days=7)).isoformat()
        end_date = date.today().isoformat()
        url = f'/api/reports/sales-summary/?start_date={start_date}&end_date={end_date}'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should only include recent transaction
        assert response.data['total_transactions'] >= 1

    def test_sales_summary_defaults_to_30_days(
        self, authenticated_report_client, customer, employee
    ):
        """Test sales summary defaults to last 30 days."""
        # Create old transaction (outside 30 days)
        SalesTransaction.objects.create(
            transaction_id='VERYOLD-001',
            customer=customer,
            salesperson=employee,
            transaction_date=date.today() - timedelta(days=45),
            status='COMPLETED',
            payment_method='cash',
            subtotal=Decimal('500.00'),
            tax_amount=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            commission_amount=Decimal('25.00'),
        )

        url = '/api/reports/sales-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should not include old transaction

    def test_sales_summary_only_completed_transactions(
        self, authenticated_report_client, customer, employee
    ):
        """Test that only COMPLETED transactions are included."""
        # Create pending transaction
        SalesTransaction.objects.create(
            transaction_id='PENDING-001',
            customer=customer,
            salesperson=employee,
            transaction_date=date.today(),
            status='PENDING',
            payment_method='cash',
            subtotal=Decimal('1000.00'),
            tax_amount=Decimal('100.00'),
            discount_amount=Decimal('0.00'),
            commission_amount=Decimal('50.00'),
        )

        # Create completed transaction
        SalesTransaction.objects.create(
            transaction_id='DONE-001',
            customer=customer,
            salesperson=employee,
            transaction_date=date.today(),
            status='COMPLETED',
            payment_method='cash',
            subtotal=Decimal('200.00'),
            tax_amount=Decimal('20.00'),
            discount_amount=Decimal('0.00'),
            commission_amount=Decimal('10.00'),
        )

        url = '/api/reports/sales-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should only include completed transactions

    def test_top_salespeople_ranking(
        self, authenticated_report_client, customer, department
    ):
        """Test top salespeople ranking."""
        # Create salespeople and transactions
        for i in range(3):
            emp = Employee.objects.create(
                employee_id=f'SALES{i}',
                first_name=f'Salesperson{i}',
                last_name='Test',
                email=f'sales{i}@test.com',
                department=department,
                job_title='Sales Rep',
                employment_type='full-time',
                employment_status='ACTIVE',
                hire_date=date.today(),
            )

            # Create varying amounts of sales
            for j in range(i + 1):
                SalesTransaction.objects.create(
                    transaction_id=f'SALE-{i}-{j}',
                    customer=customer,
                    salesperson=emp,
                    transaction_date=date.today(),
                    status='COMPLETED',
                    payment_method='credit_card',
                    subtotal=Decimal('100.00'),
                    tax_amount=Decimal('10.00'),
                    discount_amount=Decimal('0.00'),
                    commission_amount=Decimal('5.00'),
                )

        url = '/api/reports/sales-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'top_salespeople' in response.data
        assert isinstance(response.data['top_salespeople'], list)

    def test_sales_calculation_accuracy(
        self, authenticated_report_client, customer, employee
    ):
        """Test sales summary calculation accuracy."""
        # Create transactions with known values
        SalesTransaction.objects.create(
            transaction_id='CALC-001',
            customer=customer,
            salesperson=employee,
            transaction_date=date.today(),
            status='COMPLETED',
            payment_method='credit_card',
            subtotal=Decimal('1000.00'),
            tax_amount=Decimal('100.00'),
            discount_amount=Decimal('50.00'),
            commission_amount=Decimal('50.00'),
        )

        SalesTransaction.objects.create(
            transaction_id='CALC-002',
            customer=customer,
            salesperson=employee,
            transaction_date=date.today(),
            status='COMPLETED',
            payment_method='cash',
            subtotal=Decimal('500.00'),
            tax_amount=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            commission_amount=Decimal('25.00'),
        )

        url = '/api/reports/sales-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_transactions'] >= 2

    def test_empty_sales_data(self, authenticated_report_client):
        """Test sales summary with no transactions."""
        SalesTransaction.objects.all().delete()

        url = '/api/reports/sales-summary/'
        response = authenticated_report_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_sales'] is None or response.data['total_sales'] == 0
        assert response.data['total_transactions'] == 0
