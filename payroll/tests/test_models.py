"""Unit tests for payroll models - CRITICAL for financial accuracy."""
import pytest
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
from payroll.models import PayrollPeriod, Paycheck, TaxRate, Deduction


@pytest.mark.unit
class TestPayrollPeriod:
    """Tests for PayrollPeriod model."""

    def test_create_payroll_period(self, payroll_period):
        """Test creating a payroll period."""
        assert payroll_period.status == 'DRAFT'
        assert str(payroll_period) == 'Payroll 2024-01-01 to 2024-01-15'

    def test_payroll_period_unique_dates(self, payroll_period, payroll_user):
        """Test that period dates must be unique."""
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            PayrollPeriod.objects.create(
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 15),
                pay_date=date(2024, 1, 19),
                status='DRAFT',
                created_by=payroll_user,
            )

    def test_total_gross_pay(self, payroll_period, paycheck):
        """Test total gross pay calculation."""
        total = payroll_period.total_gross_pay
        assert total == paycheck.gross_pay

    def test_total_net_pay(self, payroll_period, paycheck):
        """Test total net pay calculation."""
        total = payroll_period.total_net_pay
        assert total == paycheck.net_pay


@pytest.mark.unit
class TestPaycheck:
    """Tests for Paycheck model - CRITICAL financial calculations."""

    def test_create_paycheck(self, paycheck):
        """Test creating a paycheck."""
        assert paycheck.regular_hours == Decimal('80.00')
        assert paycheck.regular_pay == Decimal('2307.69')

    def test_gross_pay_calculation(self, paycheck):
        """Test gross pay is calculated correctly."""
        expected_gross = (
            paycheck.regular_pay +
            paycheck.overtime_pay +
            paycheck.bonus +
            paycheck.commission
        )
        assert paycheck.gross_pay == expected_gross

    def test_total_taxes_calculation(self, paycheck):
        """Test total taxes calculation."""
        expected_taxes = (
            paycheck.federal_income_tax +
            paycheck.state_income_tax +
            paycheck.social_security_tax +
            paycheck.medicare_tax
        )
        assert paycheck.total_taxes == expected_taxes

    def test_total_deductions_calculation(self, paycheck):
        """Test total deductions calculation (excluding taxes)."""
        expected_deductions = (
            paycheck.health_insurance +
            paycheck.dental_insurance +
            paycheck.vision_insurance +
            paycheck.retirement_contribution +
            paycheck.other_deductions
        )
        assert paycheck.total_deductions == expected_deductions

    def test_net_pay_calculation(self, paycheck):
        """Test net pay calculation - CRITICAL."""
        expected_net = (
            paycheck.gross_pay -
            paycheck.total_taxes -
            paycheck.total_deductions
        )
        assert paycheck.net_pay == expected_net

    def test_net_pay_accuracy(self, paycheck):
        """Test net pay calculation accuracy to 2 decimal places."""
        # Gross pay: 2807.69
        # Taxes: 635.94
        # Deductions: 215.38
        # Net: 1956.37
        assert paycheck.gross_pay == Decimal('2807.69')
        assert paycheck.total_taxes == Decimal('635.94')
        assert paycheck.total_deductions == Decimal('215.38')
        assert paycheck.net_pay == Decimal('1956.37')

    def test_paycheck_auto_save_calculations(self, payroll_employee, payroll_period):
        """Test that gross and net pay are calculated on save."""
        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=Decimal('1000.00'),
            overtime_pay=Decimal('200.00'),
            bonus=Decimal('100.00'),
            federal_income_tax=Decimal('150.00'),
            social_security_tax=Decimal('80.00'),
        )
        # Gross should be automatically calculated
        assert paycheck.gross_pay == Decimal('1300.00')
        # Net should be automatically calculated
        assert paycheck.net_pay == Decimal('1070.00')

    def test_overtime_calculation(self, payroll_employee, payroll_period):
        """Test overtime pay calculation."""
        hourly_rate = Decimal('28.85')  # ~$60k/year bi-weekly
        overtime_rate = hourly_rate * Decimal('1.5')
        overtime_hours = Decimal('10.00')
        overtime_pay = overtime_rate * overtime_hours

        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_hours=Decimal('80.00'),
            regular_pay=Decimal('2307.69'),
            overtime_hours=overtime_hours,
            overtime_pay=overtime_pay,
        )

        assert paycheck.overtime_pay == Decimal('432.75')

    def test_commission_calculation(self, payroll_employee, payroll_period):
        """Test commission is included in gross pay."""
        commission = Decimal('1500.00')
        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=Decimal('2307.69'),
            commission=commission,
        )
        assert paycheck.gross_pay == Decimal('3807.69')

    def test_zero_hours_paycheck(self, payroll_employee, payroll_period):
        """Test paycheck with zero hours (edge case)."""
        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_hours=Decimal('0.00'),
            regular_pay=Decimal('0.00'),
        )
        assert paycheck.gross_pay == Decimal('0.00')
        assert paycheck.net_pay == Decimal('0.00')


@pytest.mark.unit
class TestTaxRate:
    """Tests for TaxRate model."""

    def test_create_tax_rate(self, federal_tax_rate):
        """Test creating a tax rate."""
        assert federal_tax_rate.tax_type == 'FEDERAL_INCOME'
        assert federal_tax_rate.rate == Decimal('12.0000')
        assert federal_tax_rate.is_active is True

    def test_tax_rate_string_representation(self, federal_tax_rate):
        """Test tax rate string representation."""
        expected = "Federal Income Tax - 2024 (12.0000%)"
        assert str(federal_tax_rate) == expected

    def test_rate_positive(self, federal_tax_rate):
        """Test that tax rate must be positive."""
        federal_tax_rate.rate = Decimal('-1.0000')
        with pytest.raises(ValidationError):
            federal_tax_rate.full_clean()


@pytest.mark.unit
class TestDeduction:
    """Tests for Deduction model."""

    def test_create_deduction(self, health_deduction):
        """Test creating a deduction."""
        assert health_deduction.name == 'Health Insurance'
        assert health_deduction.deduction_type == 'HEALTH'
        assert health_deduction.default_amount == Decimal('100.00')
        assert health_deduction.is_pre_tax is True

    def test_percentage_deduction(self, db):
        """Test percentage-based deduction."""
        deduction = Deduction.objects.create(
            name='401k Contribution',
            deduction_type='RETIREMENT',
            default_amount=Decimal('5.00'),  # 5%
            is_percentage=True,
            frequency='PER_PAYCHECK',
            is_pre_tax=True,
        )
        assert deduction.is_percentage is True
        assert deduction.default_amount == Decimal('5.00')
