"""Admin configuration for sales app."""
from django.contrib import admin
from .models import Customer, Product, SalesTransaction, SalesTransactionItem, CommissionPayment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'name', 'customer_type', 'email', 'is_active']
    list_filter = ['customer_type', 'is_active']
    search_fields = ['customer_id', 'name', 'email', 'company']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'product_type', 'unit_price', 'commission_rate', 'is_active']
    list_filter = ['product_type', 'is_active', 'is_taxable']
    search_fields = ['sku', 'name', 'description']
    readonly_fields = ['profit_margin']


class SalesTransactionItemInline(admin.TabularInline):
    model = SalesTransactionItem
    extra = 1
    readonly_fields = ['line_total', 'commission_amount']


@admin.register(SalesTransaction)
class SalesTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id',
        'customer',
        'salesperson',
        'transaction_date',
        'total_amount',
        'status',
        'commission_paid'
    ]
    list_filter = ['status', 'payment_method', 'commission_paid', 'transaction_date']
    search_fields = ['transaction_id', 'customer__name', 'salesperson__first_name', 'salesperson__last_name']
    readonly_fields = ['total_amount', 'commission_amount', 'created_at', 'updated_at']
    inlines = [SalesTransactionItemInline]


@admin.register(SalesTransactionItem)
class SalesTransactionItemAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'product', 'quantity', 'unit_price', 'line_total', 'commission_amount']
    list_filter = ['product__product_type']
    search_fields = ['transaction__transaction_id', 'product__name']
    readonly_fields = ['line_total', 'commission_amount']


@admin.register(CommissionPayment)
class CommissionPaymentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payment_date', 'period_start', 'period_end', 'commission_amount', 'status']
    list_filter = ['status', 'payment_date']
    search_fields = ['employee__first_name', 'employee__last_name']
