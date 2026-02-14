"""Views for employees app."""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Department, Employee, Address
from .serializers import DepartmentSerializer, EmployeeSerializer, AddressSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department model."""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'created_at']


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet for Employee model."""
    queryset = Employee.objects.select_related('department', 'user').prefetch_related('addresses')
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employment_status', 'employment_type', 'department', 'pay_frequency']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email']
    ordering_fields = ['employee_id', 'last_name', 'hire_date', 'base_salary']


class AddressViewSet(viewsets.ModelViewSet):
    """ViewSet for Address model."""
    queryset = Address.objects.select_related('employee')
    serializer_class = AddressSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['employee', 'address_type', 'state', 'is_primary']
    search_fields = ['city', 'state', 'zip_code']
