"""Serializers for employees app."""
from rest_framework import serializers
from .models import Department, Employee, Address


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""

    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'manager', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model."""

    class Meta:
        model = Address
        fields = [
            'id', 'employee', 'address_type', 'street_address_1', 'street_address_2',
            'city', 'state', 'zip_code', 'country', 'is_primary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model."""
    full_name = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'employee_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'date_of_birth', 'ssn_last_four',
            'department', 'job_title', 'employment_type', 'employment_status', 'is_active',
            'hire_date', 'termination_date',
            'base_salary', 'pay_frequency', 'hourly_rate',
            'tax_filing_status', 'federal_allowances', 'state_allowances', 'additional_withholding',
            'has_health_insurance', 'has_dental_insurance', 'has_vision_insurance',
            'retirement_contribution_percent',
            'addresses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'full_name', 'is_active']
