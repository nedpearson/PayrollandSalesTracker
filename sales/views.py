"""Views for sales app."""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Customer, Product, SalesTransaction, SalesTransactionItem, CommissionPayment
from .serializers import (
    CustomerSerializer, ProductSerializer, SalesTransactionSerializer,
    SalesTransactionItemSerializer, CommissionPaymentSerializer
)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer model."""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer_type', 'is_active']
    search_fields = ['customer_id', 'name', 'email', 'company']
    ordering_fields = ['name', 'customer_id', 'created_at']


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product_type', 'is_active', 'is_taxable']
    search_fields = ['sku', 'name', 'description']
    ordering_fields = ['name', 'unit_price', 'created_at']


class SalesTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for SalesTransaction model."""
    queryset = SalesTransaction.objects.select_related(
        'customer', 'salesperson'
    ).prefetch_related('items')
    serializer_class = SalesTransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'salesperson', 'customer', 'commission_paid']
    search_fields = ['transaction_id', 'customer__name', 'salesperson__first_name', 'salesperson__last_name']
    ordering_fields = ['transaction_date', 'total_amount', 'created_at']


class SalesTransactionItemViewSet(viewsets.ModelViewSet):
    """ViewSet for SalesTransactionItem model."""
    queryset = SalesTransactionItem.objects.select_related('transaction', 'product')
    serializer_class = SalesTransactionItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['transaction', 'product']
    search_fields = ['product__name', 'product__sku']


class CommissionPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for CommissionPayment model."""
    queryset = CommissionPayment.objects.select_related('employee')
    serializer_class = CommissionPaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'status', 'payment_date']
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering_fields = ['payment_date', 'commission_amount']
