"""Serializers for sales app."""
from rest_framework import serializers
from .models import Customer, Product, SalesTransaction, SalesTransactionItem, CommissionPayment


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""

    class Meta:
        model = Customer
        fields = [
            'id', 'customer_id', 'name', 'customer_type', 'email', 'phone',
            'company', 'tax_id', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    profit_margin = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'product_type',
            'unit_price', 'cost', 'profit_margin', 'commission_rate',
            'is_taxable', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['profit_margin', 'created_at', 'updated_at']


class SalesTransactionItemSerializer(serializers.ModelSerializer):
    """Serializer for SalesTransactionItem model."""
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = SalesTransactionItem
        fields = [
            'id', 'transaction', 'product', 'product_name', 'quantity',
            'unit_price', 'discount_amount', 'line_total',
            'commission_rate', 'commission_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['line_total', 'commission_amount', 'created_at', 'updated_at']


class SalesTransactionSerializer(serializers.ModelSerializer):
    """Serializer for SalesTransaction model."""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    salesperson_name = serializers.CharField(source='salesperson.full_name', read_only=True)
    items = SalesTransactionItemSerializer(many=True, read_only=True)

    class Meta:
        model = SalesTransaction
        fields = [
            'id', 'transaction_id', 'customer', 'customer_name',
            'salesperson', 'salesperson_name', 'transaction_date',
            'status', 'payment_method',
            'subtotal', 'tax_amount', 'discount_amount', 'total_amount',
            'commission_amount', 'commission_paid', 'commission_paid_date',
            'items', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_amount', 'commission_amount', 'created_at', 'updated_at']


class CommissionPaymentSerializer(serializers.ModelSerializer):
    """Serializer for CommissionPayment model."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = CommissionPayment
        fields = [
            'id', 'employee', 'employee_name', 'payment_date',
            'period_start', 'period_end', 'total_sales', 'commission_amount',
            'status', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
