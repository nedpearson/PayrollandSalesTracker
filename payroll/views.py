"""Views for payroll app."""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import PayrollPeriod, Paycheck, TaxRate, Deduction, EmployeeDeduction
from .serializers import (
    PayrollPeriodSerializer, PaycheckSerializer, TaxRateSerializer,
    DeductionSerializer, EmployeeDeductionSerializer
)


class PayrollPeriodViewSet(viewsets.ModelViewSet):
    """ViewSet for PayrollPeriod model."""
    queryset = PayrollPeriod.objects.all()
    serializer_class = PayrollPeriodSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'period_start', 'period_end']
    ordering_fields = ['period_start', 'period_end', 'pay_date']


class PaycheckViewSet(viewsets.ModelViewSet):
    """ViewSet for Paycheck model."""
    queryset = Paycheck.objects.select_related('employee', 'payroll_period')
    serializer_class = PaycheckSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'payroll_period', 'payroll_period__status']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    ordering_fields = ['gross_pay', 'net_pay', 'payroll_period__period_start']


class TaxRateViewSet(viewsets.ModelViewSet):
    """ViewSet for TaxRate model."""
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tax_type', 'year', 'state', 'is_active']
    ordering_fields = ['tax_type', 'year', 'rate']


class DeductionViewSet(viewsets.ModelViewSet):
    """ViewSet for Deduction model."""
    queryset = Deduction.objects.all()
    serializer_class = DeductionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['deduction_type', 'is_active', 'frequency']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'deduction_type']


class EmployeeDeductionViewSet(viewsets.ModelViewSet):
    """ViewSet for EmployeeDeduction model."""
    queryset = EmployeeDeduction.objects.select_related('employee', 'deduction')
    serializer_class = EmployeeDeductionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['employee', 'deduction', 'is_active']
    search_fields = ['employee__first_name', 'employee__last_name', 'deduction__name']
