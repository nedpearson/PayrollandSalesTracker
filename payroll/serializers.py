"""Serializers for payroll app."""
from rest_framework import serializers
from .models import PayrollPeriod, Paycheck, TaxRate, Deduction, EmployeeDeduction


class PayrollPeriodSerializer(serializers.ModelSerializer):
    """Serializer for PayrollPeriod model."""
    total_gross_pay = serializers.ReadOnlyField()
    total_net_pay = serializers.ReadOnlyField()

    class Meta:
        model = PayrollPeriod
        fields = [
            'id', 'period_start', 'period_end', 'pay_date', 'status',
            'created_by', 'approved_by', 'approved_at',
            'total_gross_pay', 'total_net_pay',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_gross_pay', 'total_net_pay']


class PaycheckSerializer(serializers.ModelSerializer):
    """Serializer for Paycheck model."""
    total_taxes = serializers.ReadOnlyField()
    total_deductions = serializers.ReadOnlyField()
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = Paycheck
        fields = [
            'id', 'employee', 'employee_name', 'payroll_period',
            'regular_hours', 'overtime_hours', 'regular_pay', 'overtime_pay',
            'bonus', 'commission', 'gross_pay',
            'federal_income_tax', 'state_income_tax', 'social_security_tax', 'medicare_tax',
            'health_insurance', 'dental_insurance', 'vision_insurance',
            'retirement_contribution', 'other_deductions',
            'total_taxes', 'total_deductions', 'net_pay',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['gross_pay', 'net_pay', 'total_taxes', 'total_deductions', 'created_at', 'updated_at']


class TaxRateSerializer(serializers.ModelSerializer):
    """Serializer for TaxRate model."""

    class Meta:
        model = TaxRate
        fields = [
            'id', 'tax_type', 'state', 'year', 'rate',
            'income_min', 'income_max', 'additional_amount',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DeductionSerializer(serializers.ModelSerializer):
    """Serializer for Deduction model."""

    class Meta:
        model = Deduction
        fields = [
            'id', 'name', 'deduction_type', 'description',
            'default_amount', 'is_percentage', 'frequency', 'is_pre_tax',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EmployeeDeductionSerializer(serializers.ModelSerializer):
    """Serializer for EmployeeDeduction model."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    deduction_name = serializers.CharField(source='deduction.name', read_only=True)

    class Meta:
        model = EmployeeDeduction
        fields = [
            'id', 'employee', 'employee_name', 'deduction', 'deduction_name',
            'amount', 'start_date', 'end_date', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
