"""Tests for payroll serializers."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from payroll.models import PayrollPeriod, Paycheck, TaxRate, Deduction, EmployeeDeduction
from payroll.serializers import (
    PayrollPeriodSerializer,
    PaycheckSerializer,
    TaxRateSerializer,
    DeductionSerializer,
    EmployeeDeductionSerializer,
)


@pytest.mark.django_db
class TestPayrollPeriodSerializer:
    """Tests for PayrollPeriodSerializer."""

    def test_serialization(self, payroll_period):
        """Test payroll period serialization."""
        serializer = PayrollPeriodSerializer(payroll_period)
        data = serializer.data

        assert data['id'] == payroll_period.id
        assert 'period_start' in data
        assert 'period_end' in data
        assert 'pay_date' in data
        assert data['status'] == payroll_period.status
        assert 'total_gross_pay' in data
        assert 'total_net_pay' in data

    def test_total_gross_pay_read_only(self, payroll_period_with_paychecks):
        """Test that total_gross_pay is read-only and computed."""
        serializer = PayrollPeriodSerializer(payroll_period_with_paychecks)
        data = serializer.data

        assert 'total_gross_pay' in data
        # total_gross_pay should be computed from related paychecks
        assert isinstance(data['total_gross_pay'], str)

    def test_total_net_pay_read_only(self, payroll_period_with_paychecks):
        """Test that total_net_pay is read-only and computed."""
        serializer = PayrollPeriodSerializer(payroll_period_with_paychecks)
        data = serializer.data

        assert 'total_net_pay' in data
        assert isinstance(data['total_net_pay'], str)

    def test_deserialization(self, user):
        """Test payroll period deserialization."""
        data = {
            'period_start': '2024-01-01',
            'period_end': '2024-01-15',
            'pay_date': '2024-01-19',
            'status': 'draft',
            'created_by': user.id,
        }
        serializer = PayrollPeriodSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        period = serializer.save()

        assert period.status == 'draft'
        assert period.period_start == date(2024, 1, 1)
        assert period.period_end == date(2024, 1, 15)

    def test_status_choices(self, user):
        """Test valid status choices."""
        valid_statuses = ['draft', 'processing', 'approved', 'paid']

        for status in valid_statuses:
            data = {
                'period_start': '2024-01-01',
                'period_end': '2024-01-15',
                'pay_date': '2024-01-19',
                'status': status,
                'created_by': user.id,
            }
            serializer = PayrollPeriodSerializer(data=data)
            assert serializer.is_valid(), f"Status {status} should be valid"

    def test_read_only_fields(self, payroll_period):
        """Test that read-only fields cannot be updated."""
        original_created_at = payroll_period.created_at
        data = {
            'status': 'processing',
            'created_at': date.today(),  # Try to update read-only field
        }
        serializer = PayrollPeriodSerializer(payroll_period, data=data, partial=True)

        assert serializer.is_valid()
        serializer.save()

        payroll_period.refresh_from_db()
        assert payroll_period.created_at == original_created_at

    def test_approval_fields(self, payroll_period, user):
        """Test approval-related fields."""
        data = {
            'status': 'approved',
            'approved_by': user.id,
            'approved_at': date.today(),
        }
        serializer = PayrollPeriodSerializer(payroll_period, data=data, partial=True)

        assert serializer.is_valid()
        period = serializer.save()

        assert period.status == 'approved'
        assert period.approved_by == user


@pytest.mark.django_db
class TestPaycheckSerializer:
    """Tests for PaycheckSerializer."""

    def test_serialization(self, paycheck):
        """Test paycheck serialization."""
        serializer = PaycheckSerializer(paycheck)
        data = serializer.data

        assert data['id'] == paycheck.id
        assert data['employee'] == paycheck.employee.id
        assert 'employee_name' in data
        assert 'gross_pay' in data
        assert 'net_pay' in data
        assert 'total_taxes' in data
        assert 'total_deductions' in data

    def test_employee_name_read_only(self, paycheck):
        """Test that employee_name is read-only and computed."""
        serializer = PaycheckSerializer(paycheck)
        data = serializer.data

        assert data['employee_name'] == paycheck.employee.full_name

    def test_total_taxes_computed(self, paycheck):
        """Test that total_taxes is computed correctly."""
        serializer = PaycheckSerializer(paycheck)
        data = serializer.data

        expected_total = (
            paycheck.federal_income_tax +
            paycheck.state_income_tax +
            paycheck.social_security_tax +
            paycheck.medicare_tax
        )
        assert Decimal(data['total_taxes']) == expected_total

    def test_total_deductions_computed(self, paycheck):
        """Test that total_deductions is computed correctly."""
        serializer = PaycheckSerializer(paycheck)
        data = serializer.data

        expected_total = (
            paycheck.health_insurance +
            paycheck.dental_insurance +
            paycheck.vision_insurance +
            paycheck.retirement_contribution +
            paycheck.other_deductions
        )
        assert Decimal(data['total_deductions']) == expected_total

    def test_deserialization(self, employee, payroll_period):
        """Test paycheck deserialization."""
        data = {
            'employee': employee.id,
            'payroll_period': payroll_period.id,
            'regular_hours': '80.00',
            'overtime_hours': '5.00',
            'regular_pay': '3200.00',
            'overtime_pay': '300.00',
            'bonus': '0.00',
            'commission': '0.00',
            'federal_income_tax': '700.00',
            'state_income_tax': '175.00',
            'social_security_tax': '217.00',
            'medicare_tax': '50.75',
            'health_insurance': '200.00',
            'dental_insurance': '50.00',
            'vision_insurance': '25.00',
            'retirement_contribution': '175.00',
            'other_deductions': '0.00',
            'notes': 'Regular paycheck',
        }
        serializer = PaycheckSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        paycheck = serializer.save()

        assert paycheck.employee == employee
        assert paycheck.regular_hours == Decimal('80.00')
        assert paycheck.overtime_hours == Decimal('5.00')

    def test_gross_pay_read_only(self, employee, payroll_period):
        """Test that gross_pay is read-only and computed."""
        data = {
            'employee': employee.id,
            'payroll_period': payroll_period.id,
            'regular_hours': '80.00',
            'regular_pay': '3200.00',
            'overtime_pay': '0.00',
            'bonus': '500.00',
            'commission': '0.00',
            'gross_pay': '9999.99',  # Try to set manually (should be ignored)
            'federal_income_tax': '0.00',
            'state_income_tax': '0.00',
            'social_security_tax': '0.00',
            'medicare_tax': '0.00',
            'health_insurance': '0.00',
            'dental_insurance': '0.00',
            'vision_insurance': '0.00',
            'retirement_contribution': '0.00',
            'other_deductions': '0.00',
        }
        serializer = PaycheckSerializer(data=data)

        assert serializer.is_valid()
        paycheck = serializer.save()

        # gross_pay should be computed, not the manually set value
        expected_gross = Decimal('3200.00') + Decimal('0.00') + Decimal('500.00') + Decimal('0.00')
        assert paycheck.gross_pay == expected_gross
        assert paycheck.gross_pay != Decimal('9999.99')

    def test_net_pay_read_only(self, paycheck):
        """Test that net_pay is read-only and computed."""
        serializer = PaycheckSerializer(paycheck)
        data = serializer.data

        expected_net = paycheck.gross_pay - Decimal(data['total_taxes']) - Decimal(data['total_deductions'])
        assert abs(Decimal(data['net_pay']) - expected_net) < Decimal('0.01')

    def test_overtime_pay(self, employee, payroll_period):
        """Test paycheck with overtime."""
        data = {
            'employee': employee.id,
            'payroll_period': payroll_period.id,
            'regular_hours': '80.00',
            'overtime_hours': '10.00',
            'regular_pay': '3200.00',
            'overtime_pay': '600.00',  # 10 hours at 1.5x rate
            'bonus': '0.00',
            'commission': '0.00',
            'federal_income_tax': '0.00',
            'state_income_tax': '0.00',
            'social_security_tax': '0.00',
            'medicare_tax': '0.00',
            'health_insurance': '0.00',
            'dental_insurance': '0.00',
            'vision_insurance': '0.00',
            'retirement_contribution': '0.00',
            'other_deductions': '0.00',
        }
        serializer = PaycheckSerializer(data=data)

        assert serializer.is_valid()
        paycheck = serializer.save()

        assert paycheck.overtime_hours == Decimal('10.00')
        assert paycheck.overtime_pay == Decimal('600.00')

    def test_bonus_and_commission(self, employee, payroll_period):
        """Test paycheck with bonus and commission."""
        data = {
            'employee': employee.id,
            'payroll_period': payroll_period.id,
            'regular_hours': '80.00',
            'regular_pay': '3200.00',
            'overtime_hours': '0.00',
            'overtime_pay': '0.00',
            'bonus': '1000.00',
            'commission': '500.00',
            'federal_income_tax': '0.00',
            'state_income_tax': '0.00',
            'social_security_tax': '0.00',
            'medicare_tax': '0.00',
            'health_insurance': '0.00',
            'dental_insurance': '0.00',
            'vision_insurance': '0.00',
            'retirement_contribution': '0.00',
            'other_deductions': '0.00',
        }
        serializer = PaycheckSerializer(data=data)

        assert serializer.is_valid()
        paycheck = serializer.save()

        assert paycheck.bonus == Decimal('1000.00')
        assert paycheck.commission == Decimal('500.00')
        assert paycheck.gross_pay == Decimal('4700.00')


@pytest.mark.django_db
class TestTaxRateSerializer:
    """Tests for TaxRateSerializer."""

    def test_serialization(self):
        """Test tax rate serialization."""
        tax_rate = TaxRate.objects.create(
            tax_type='federal',
            year=2024,
            rate=Decimal('0.22'),
            income_min=Decimal('44725.00'),
            income_max=Decimal('95375.00'),
            additional_amount=Decimal('5147.00'),
            is_active=True,
        )
        serializer = TaxRateSerializer(tax_rate)
        data = serializer.data

        assert data['tax_type'] == 'federal'
        assert Decimal(data['rate']) == Decimal('0.22')
        assert data['year'] == 2024

    def test_deserialization(self):
        """Test tax rate deserialization."""
        data = {
            'tax_type': 'state',
            'state': 'CA',
            'year': 2024,
            'rate': '0.093',
            'income_min': '61214.00',
            'income_max': '312686.00',
            'is_active': True,
        }
        serializer = TaxRateSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        tax_rate = serializer.save()

        assert tax_rate.tax_type == 'state'
        assert tax_rate.state == 'CA'
        assert tax_rate.rate == Decimal('0.093')


@pytest.mark.django_db
class TestDeductionSerializer:
    """Tests for DeductionSerializer."""

    def test_serialization(self):
        """Test deduction serialization."""
        deduction = Deduction.objects.create(
            name='401(k) Contribution',
            deduction_type='retirement',
            description='Employee 401(k) retirement contribution',
            default_amount=Decimal('100.00'),
            is_percentage=False,
            frequency='per-paycheck',
            is_pre_tax=True,
            is_active=True,
        )
        serializer = DeductionSerializer(deduction)
        data = serializer.data

        assert data['name'] == '401(k) Contribution'
        assert data['deduction_type'] == 'retirement'
        assert data['is_pre_tax'] is True

    def test_deserialization(self):
        """Test deduction deserialization."""
        data = {
            'name': 'Health Insurance',
            'deduction_type': 'insurance',
            'description': 'Monthly health insurance premium',
            'default_amount': '200.00',
            'is_percentage': False,
            'frequency': 'monthly',
            'is_pre_tax': True,
            'is_active': True,
        }
        serializer = DeductionSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        deduction = serializer.save()

        assert deduction.name == 'Health Insurance'
        assert deduction.default_amount == Decimal('200.00')

    def test_percentage_deduction(self):
        """Test percentage-based deduction."""
        data = {
            'name': 'Retirement %',
            'deduction_type': 'retirement',
            'default_amount': '5.00',  # 5%
            'is_percentage': True,
            'frequency': 'per-paycheck',
            'is_pre_tax': True,
            'is_active': True,
        }
        serializer = DeductionSerializer(data=data)

        assert serializer.is_valid()
        deduction = serializer.save()

        assert deduction.is_percentage is True
        assert deduction.default_amount == Decimal('5.00')


@pytest.mark.django_db
class TestEmployeeDeductionSerializer:
    """Tests for EmployeeDeductionSerializer."""

    def test_serialization(self, employee):
        """Test employee deduction serialization."""
        deduction = Deduction.objects.create(
            name='Test Deduction',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            is_percentage=False,
            frequency='per-paycheck',
            is_active=True,
        )
        emp_deduction = EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('75.00'),
            start_date=date.today(),
            is_active=True,
        )
        serializer = EmployeeDeductionSerializer(emp_deduction)
        data = serializer.data

        assert data['employee'] == employee.id
        assert data['employee_name'] == employee.full_name
        assert data['deduction'] == deduction.id
        assert data['deduction_name'] == deduction.name
        assert Decimal(data['amount']) == Decimal('75.00')

    def test_deserialization(self, employee):
        """Test employee deduction deserialization."""
        deduction = Deduction.objects.create(
            name='Custom Deduction',
            deduction_type='other',
            default_amount=Decimal('100.00'),
            is_percentage=False,
            frequency='per-paycheck',
            is_active=True,
        )
        data = {
            'employee': employee.id,
            'deduction': deduction.id,
            'amount': '150.00',
            'start_date': '2024-01-01',
            'is_active': True,
        }
        serializer = EmployeeDeductionSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        emp_deduction = serializer.save()

        assert emp_deduction.employee == employee
        assert emp_deduction.deduction == deduction
        assert emp_deduction.amount == Decimal('150.00')

    def test_employee_name_read_only(self, employee):
        """Test that employee_name is read-only."""
        deduction = Deduction.objects.create(
            name='Test',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            is_percentage=False,
            frequency='per-paycheck',
            is_active=True,
        )
        emp_deduction = EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('50.00'),
            is_active=True,
        )
        serializer = EmployeeDeductionSerializer(emp_deduction)
        data = serializer.data

        assert data['employee_name'] == employee.full_name

    def test_deduction_name_read_only(self, employee):
        """Test that deduction_name is read-only."""
        deduction = Deduction.objects.create(
            name='Deduction Name Test',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            is_percentage=False,
            frequency='per-paycheck',
            is_active=True,
        )
        emp_deduction = EmployeeDeduction.objects.create(
            employee=employee,
            deduction=deduction,
            amount=Decimal('50.00'),
            is_active=True,
        )
        serializer = EmployeeDeductionSerializer(emp_deduction)
        data = serializer.data

        assert data['deduction_name'] == 'Deduction Name Test'

    def test_optional_end_date(self, employee):
        """Test employee deduction with optional end date."""
        deduction = Deduction.objects.create(
            name='Temporary Deduction',
            deduction_type='other',
            default_amount=Decimal('50.00'),
            is_percentage=False,
            frequency='per-paycheck',
            is_active=True,
        )
        data = {
            'employee': employee.id,
            'deduction': deduction.id,
            'amount': '50.00',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'is_active': True,
        }
        serializer = EmployeeDeductionSerializer(data=data)

        assert serializer.is_valid()
        emp_deduction = serializer.save()

        assert emp_deduction.end_date == date(2024, 12, 31)
