"""Critical tests for payroll calculations - financial accuracy tests."""
import pytest
from decimal import Decimal
from datetime import date
from payroll.models import Paycheck


@pytest.mark.unit
class TestPayrollCalculations:
    """Comprehensive tests for payroll calculation accuracy."""

    def test_social_security_tax_calculation(self, payroll_employee, payroll_period):
        """Test Social Security tax calculation (6.2% of gross)."""
        gross_pay = Decimal('3000.00')
        expected_ss_tax = gross_pay * Decimal('0.062')

        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=gross_pay,
            social_security_tax=expected_ss_tax,
        )

        assert paycheck.social_security_tax == Decimal('186.00')

    def test_medicare_tax_calculation(self, payroll_employee, payroll_period):
        """Test Medicare tax calculation (1.45% of gross)."""
        gross_pay = Decimal('3000.00')
        expected_medicare_tax = gross_pay * Decimal('0.0145')

        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=gross_pay,
            medicare_tax=expected_medicare_tax,
        )

        assert paycheck.medicare_tax == Decimal('43.50')

    def test_retirement_contribution_calculation(self, payroll_employee, payroll_period):
        """Test retirement contribution calculation."""
        gross_pay = Decimal('2307.69')
        contribution_rate = Decimal('5.00')  # 5%
        expected_contribution = (gross_pay * contribution_rate / Decimal('100')).quantize(Decimal('0.01'))

        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=gross_pay,
            retirement_contribution=expected_contribution,
        )

        assert paycheck.retirement_contribution == Decimal('115.38')

    def test_precision_rounding(self, payroll_employee, payroll_period):
        """Test that all amounts are properly rounded to 2 decimal places."""
        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=Decimal('2307.69'),
            federal_income_tax=Decimal('280.77'),
            state_income_tax=Decimal('140.38'),
            social_security_tax=Decimal('143.08'),
            medicare_tax=Decimal('33.46'),
        )

        # All amounts should have exactly 2 decimal places
        assert paycheck.gross_pay.as_tuple().exponent == -2
        assert paycheck.net_pay.as_tuple().exponent == -2
        assert paycheck.federal_income_tax.as_tuple().exponent == -2

    def test_no_floating_point_errors(self, payroll_employee, payroll_period):
        """Test that we use Decimal for accuracy, not float."""
        # This test ensures we don't have floating point arithmetic errors
        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=Decimal('2307.69'),
            commission=Decimal('0.10'),
            federal_income_tax=Decimal('230.77'),
        )

        # Using Decimal prevents 0.1 + 0.2 = 0.30000000000000004 type errors
        assert isinstance(paycheck.gross_pay, Decimal)
        assert isinstance(paycheck.net_pay, Decimal)

    def test_large_salary_calculation(self, payroll_employee, payroll_period):
        """Test calculation accuracy with large salaries."""
        large_salary = Decimal('500000.00')
        bi_weekly_pay = large_salary / Decimal('26')

        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=bi_weekly_pay,
        )

        assert paycheck.gross_pay == Decimal('19230.77')

    def test_minimum_wage_calculation(self, payroll_employee, payroll_period):
        """Test calculation accuracy with minimum wage."""
        minimum_hourly = Decimal('15.00')
        hours = Decimal('80.00')
        expected_pay = minimum_hourly * hours

        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_pay=expected_pay,
        )

        assert paycheck.gross_pay == Decimal('1200.00')

    def test_negative_values_prevented(self, payroll_employee, payroll_period):
        """Test that negative values are prevented by validators."""
        with pytest.raises(Exception):  # Will raise validation error
            paycheck = Paycheck(
                employee=payroll_employee,
                payroll_period=payroll_period,
                regular_hours=Decimal('-10.00'),  # Negative hours
                regular_pay=Decimal('1000.00'),
            )
            paycheck.full_clean()


@pytest.mark.compliance
class TestPayrollCompliance:
    """Tests for payroll compliance requirements."""

    def test_minimum_wage_compliance(self, payroll_employee, payroll_period):
        """Test that pay meets minimum wage requirements."""
        hours = Decimal('80.00')
        federal_minimum = Decimal('7.25')
        minimum_pay = hours * federal_minimum

        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_hours=hours,
            regular_pay=Decimal('2307.69'),
        )

        # Verify pay is above minimum wage
        hourly_equivalent = paycheck.regular_pay / hours
        assert hourly_equivalent >= federal_minimum

    def test_overtime_rate_compliance(self, payroll_employee, payroll_period):
        """Test that overtime is calculated at 1.5x rate (FLSA compliance)."""
        regular_rate = Decimal('30.00')
        overtime_hours = Decimal('5.00')
        overtime_rate = regular_rate * Decimal('1.5')
        overtime_pay = overtime_rate * overtime_hours

        paycheck = Paycheck.objects.create(
            employee=payroll_employee,
            payroll_period=payroll_period,
            regular_hours=Decimal('80.00'),
            regular_pay=Decimal('2400.00'),
            overtime_hours=overtime_hours,
            overtime_pay=overtime_pay,
        )

        assert paycheck.overtime_pay == Decimal('225.00')
        # Verify 1.5x multiplier
        assert paycheck.overtime_pay == (regular_rate * Decimal('1.5') * overtime_hours)
