"""Unit tests for sales models."""
import pytest
from decimal import Decimal
from datetime import datetime
from django.db import IntegrityError
from sales.models import Customer, Product, SalesTransaction, SalesTransactionItem


@pytest.mark.unit
class TestCustomer:
    """Tests for Customer model."""

    def test_create_customer(self, customer):
        """Test creating a customer."""
        assert customer.customer_id == 'CUST001'
        assert customer.name == 'Acme Corporation'
        assert str(customer) == 'CUST001 - Acme Corporation'

    def test_customer_unique_id(self, customer):
        """Test that customer ID must be unique."""
        with pytest.raises(IntegrityError):
            Customer.objects.create(
                customer_id='CUST001',  # Duplicate
                name='Different Company',
                customer_type='BUSINESS',
            )


@pytest.mark.unit
class TestProduct:
    """Tests for Product model."""

    def test_create_product(self, product):
        """Test creating a product."""
        assert product.sku == 'PROD001'
        assert product.name == 'Widget Pro'
        assert product.unit_price == Decimal('99.99')
        assert str(product) == 'PROD001 - Widget Pro'

    def test_profit_margin_calculation(self, product):
        """Test profit margin calculation."""
        # Cost: $50, Price: $99.99
        # Margin: (99.99 - 50) / 99.99 * 100 = 50.005%
        expected_margin = Decimal('50.005')
        assert abs(product.profit_margin - expected_margin) < Decimal('0.01')

    def test_product_unique_sku(self, product):
        """Test that SKU must be unique."""
        with pytest.raises(IntegrityError):
            Product.objects.create(
                sku='PROD001',  # Duplicate
                name='Different Product',
                product_type='PRODUCT',
                unit_price=Decimal('50.00'),
            )


@pytest.mark.unit
class TestSalesTransaction:
    """Tests for SalesTransaction model."""

    def test_create_transaction(self, sales_transaction):
        """Test creating a sales transaction."""
        assert sales_transaction.transaction_id == 'TXN001'
        assert sales_transaction.status == 'COMPLETED'
        assert str(sales_transaction) == 'TXN001 - Acme Corporation'

    def test_total_calculation(self, sales_transaction):
        """Test total amount calculation."""
        # Subtotal + Tax - Discount
        expected_total = Decimal('199.98') + Decimal('13.00') - Decimal('0.00')
        assert sales_transaction.total_amount == expected_total

    def test_total_with_discount(self, customer, sales_employee):
        """Test total calculation with discount."""
        transaction = SalesTransaction.objects.create(
            transaction_id='TXN002',
            customer=customer,
            salesperson=sales_employee,
            transaction_date=datetime(2024, 1, 16, 11, 0),
            status='COMPLETED',
            payment_method='CASH',
            subtotal=Decimal('200.00'),
            tax_amount=Decimal('15.00'),
            discount_amount=Decimal('20.00'),
        )
        # 200 + 15 - 20 = 195
        assert transaction.total_amount == Decimal('195.00')

    def test_transaction_unique_id(self, sales_transaction, customer, sales_employee):
        """Test that transaction ID must be unique."""
        with pytest.raises(IntegrityError):
            SalesTransaction.objects.create(
                transaction_id='TXN001',  # Duplicate
                customer=customer,
                salesperson=sales_employee,
                transaction_date=datetime.now(),
                status='PENDING',
                payment_method='CASH',
                subtotal=Decimal('100.00'),
            )


@pytest.mark.unit
class TestSalesTransactionItem:
    """Tests for SalesTransactionItem model."""

    def test_create_transaction_item(self, transaction_item):
        """Test creating a transaction item."""
        assert transaction_item.quantity == Decimal('2.00')
        assert transaction_item.unit_price == Decimal('99.99')

    def test_line_total_calculation(self, transaction_item):
        """Test line total calculation."""
        # 2 * 99.99 = 199.98
        expected_line_total = Decimal('199.98')
        assert transaction_item.line_total == expected_line_total

    def test_line_total_with_discount(self, sales_transaction, product):
        """Test line total with discount."""
        item = SalesTransactionItem.objects.create(
            transaction=sales_transaction,
            product=product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('50.00'),
            commission_rate=Decimal('10.00'),
        )
        # (5 * 100) - 50 = 450
        assert item.line_total == Decimal('450.00')

    def test_commission_calculation(self, transaction_item):
        """Test commission calculation."""
        # Line total: 199.98, Commission rate: 10%
        # Commission: 199.98 * 0.10 = 19.998 -> 20.00
        expected_commission = Decimal('20.00')
        assert transaction_item.commission_amount == expected_commission

    def test_commission_accuracy(self, sales_transaction, product):
        """Test commission calculation accuracy."""
        item = SalesTransactionItem.objects.create(
            transaction=sales_transaction,
            product=product,
            quantity=Decimal('3.00'),
            unit_price=Decimal('99.99'),
            commission_rate=Decimal('8.50'),
        )
        # Line total: 299.97
        # Commission: 299.97 * 0.085 = 25.49745 -> 25.50
        assert item.commission_amount == Decimal('25.50')


@pytest.mark.unit
class TestSalesCalculations:
    """Critical tests for sales calculations."""

    def test_sales_tax_calculation(self, customer, sales_employee, product):
        """Test sales tax calculation (e.g., 6.25% MA sales tax)."""
        subtotal = Decimal('1000.00')
        tax_rate = Decimal('0.0625')
        tax_amount = (subtotal * tax_rate).quantize(Decimal('0.01'))

        transaction = SalesTransaction.objects.create(
            transaction_id='TXN_TAX',
            customer=customer,
            salesperson=sales_employee,
            transaction_date=datetime.now(),
            status='COMPLETED',
            payment_method='CREDIT_CARD',
            subtotal=subtotal,
            tax_amount=tax_amount,
        )

        assert transaction.tax_amount == Decimal('62.50')
        assert transaction.total_amount == Decimal('1062.50')

    def test_refund_transaction(self, customer, sales_employee):
        """Test refund transaction handling."""
        transaction = SalesTransaction.objects.create(
            transaction_id='TXN_REFUND',
            customer=customer,
            salesperson=sales_employee,
            transaction_date=datetime.now(),
            status='REFUNDED',
            payment_method='CREDIT_CARD',
            subtotal=Decimal('-100.00'),  # Negative for refund
            tax_amount=Decimal('-6.25'),
        )

        assert transaction.total_amount == Decimal('-106.25')

    def test_zero_dollar_transaction(self, customer, sales_employee):
        """Test zero dollar transaction (edge case)."""
        transaction = SalesTransaction.objects.create(
            transaction_id='TXN_ZERO',
            customer=customer,
            salesperson=sales_employee,
            transaction_date=datetime.now(),
            status='COMPLETED',
            payment_method='CASH',
            subtotal=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
        )

        assert transaction.total_amount == Decimal('0.00')

    def test_high_volume_transaction(self, sales_transaction, product):
        """Test transaction with large quantities."""
        item = SalesTransactionItem.objects.create(
            transaction=sales_transaction,
            product=product,
            quantity=Decimal('1000.00'),
            unit_price=Decimal('99.99'),
            commission_rate=Decimal('5.00'),
        )

        assert item.line_total == Decimal('99990.00')
        assert item.commission_amount == Decimal('4999.50')
