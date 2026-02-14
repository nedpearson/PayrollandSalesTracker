"""Tests for sales serializers."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from sales.models import Customer, Product, SalesTransaction, SalesTransactionItem, CommissionPayment
from sales.serializers import (
    CustomerSerializer,
    ProductSerializer,
    SalesTransactionSerializer,
    SalesTransactionItemSerializer,
    CommissionPaymentSerializer,
)


@pytest.mark.django_db
class TestCustomerSerializer:
    """Tests for CustomerSerializer."""

    def test_serialization(self, customer):
        """Test customer serialization."""
        serializer = CustomerSerializer(customer)
        data = serializer.data

        assert data['id'] == customer.id
        assert data['customer_id'] == customer.customer_id
        assert data['name'] == customer.name
        assert data['email'] == customer.email
        assert data['customer_type'] == customer.customer_type
        assert data['is_active'] is True

    def test_deserialization(self):
        """Test customer deserialization."""
        data = {
            'customer_id': 'CUST999',
            'name': 'Acme Corp',
            'customer_type': 'business',
            'email': 'contact@acme.com',
            'phone': '555-0100',
            'company': 'Acme Corporation',
            'tax_id': '12-3456789',
            'is_active': True,
        }
        serializer = CustomerSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        customer = serializer.save()

        assert customer.name == 'Acme Corp'
        assert customer.customer_type == 'business'
        assert customer.tax_id == '12-3456789'

    def test_unique_customer_id_validation(self, customer):
        """Test unique customer_id constraint validation."""
        data = {
            'customer_id': customer.customer_id,  # Duplicate
            'name': 'Another Customer',
            'customer_type': 'individual',
            'email': 'another@example.com',
        }
        serializer = CustomerSerializer(data=data)

        assert not serializer.is_valid()
        assert 'customer_id' in serializer.errors

    def test_individual_customer_type(self):
        """Test creating individual customer."""
        data = {
            'customer_id': 'CUST888',
            'name': 'John Doe',
            'customer_type': 'individual',
            'email': 'john.doe@example.com',
            'phone': '555-0101',
            'is_active': True,
        }
        serializer = CustomerSerializer(data=data)

        assert serializer.is_valid()
        customer = serializer.save()

        assert customer.customer_type == 'individual'
        assert customer.company is None or customer.company == ''

    def test_business_customer_with_tax_id(self):
        """Test business customer with tax ID."""
        data = {
            'customer_id': 'CUST777',
            'name': 'Business Inc',
            'customer_type': 'business',
            'email': 'info@business.com',
            'company': 'Business Incorporated',
            'tax_id': '98-7654321',
            'is_active': True,
        }
        serializer = CustomerSerializer(data=data)

        assert serializer.is_valid()
        customer = serializer.save()

        assert customer.customer_type == 'business'
        assert customer.company == 'Business Incorporated'
        assert customer.tax_id == '98-7654321'

    def test_read_only_fields(self, customer):
        """Test that read-only fields cannot be updated."""
        original_created_at = customer.created_at
        data = {
            'name': 'Updated Name',
            'created_at': date.today(),  # Try to update read-only field
        }
        serializer = CustomerSerializer(customer, data=data, partial=True)

        assert serializer.is_valid()
        serializer.save()

        customer.refresh_from_db()
        assert customer.created_at == original_created_at

    def test_optional_fields(self):
        """Test customer with only required fields."""
        data = {
            'customer_id': 'CUST666',
            'name': 'Minimal Customer',
            'customer_type': 'individual',
        }
        serializer = CustomerSerializer(data=data)

        assert serializer.is_valid()
        customer = serializer.save()

        assert customer.email is None or customer.email == ''
        assert customer.phone is None or customer.phone == ''


@pytest.mark.django_db
class TestProductSerializer:
    """Tests for ProductSerializer."""

    def test_serialization(self, product):
        """Test product serialization."""
        serializer = ProductSerializer(product)
        data = serializer.data

        assert data['id'] == product.id
        assert data['sku'] == product.sku
        assert data['name'] == product.name
        assert Decimal(data['unit_price']) == product.unit_price
        assert 'profit_margin' in data

    def test_profit_margin_computed(self):
        """Test that profit_margin is computed correctly."""
        product = Product.objects.create(
            sku='TEST-001',
            name='Test Product',
            product_type='physical',
            unit_price=Decimal('100.00'),
            cost=Decimal('60.00'),
            is_active=True,
        )
        serializer = ProductSerializer(product)
        data = serializer.data

        # Profit margin = ((100 - 60) / 100) * 100 = 40%
        expected_margin = ((product.unit_price - product.cost) / product.unit_price) * 100
        assert abs(Decimal(data['profit_margin']) - expected_margin) < Decimal('0.01')

    def test_deserialization(self):
        """Test product deserialization."""
        data = {
            'sku': 'PROD-999',
            'name': 'Widget Pro',
            'description': 'Premium widget',
            'product_type': 'physical',
            'unit_price': '199.99',
            'cost': '120.00',
            'commission_rate': '10.00',
            'is_taxable': True,
            'is_active': True,
        }
        serializer = ProductSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        product = serializer.save()

        assert product.name == 'Widget Pro'
        assert product.unit_price == Decimal('199.99')
        assert product.commission_rate == Decimal('10.00')

    def test_unique_sku_validation(self, product):
        """Test unique SKU constraint validation."""
        data = {
            'sku': product.sku,  # Duplicate
            'name': 'Another Product',
            'product_type': 'physical',
            'unit_price': '50.00',
            'cost': '30.00',
        }
        serializer = ProductSerializer(data=data)

        assert not serializer.is_valid()
        assert 'sku' in serializer.errors

    def test_digital_product_type(self):
        """Test creating digital product."""
        data = {
            'sku': 'DIGI-001',
            'name': 'Digital Download',
            'product_type': 'digital',
            'unit_price': '29.99',
            'cost': '5.00',
            'is_taxable': False,
            'is_active': True,
        }
        serializer = ProductSerializer(data=data)

        assert serializer.is_valid()
        product = serializer.save()

        assert product.product_type == 'digital'
        assert product.is_taxable is False

    def test_service_product_type(self):
        """Test creating service product."""
        data = {
            'sku': 'SVC-001',
            'name': 'Consulting Service',
            'product_type': 'service',
            'unit_price': '150.00',
            'cost': '50.00',
            'commission_rate': '15.00',
            'is_taxable': True,
            'is_active': True,
        }
        serializer = ProductSerializer(data=data)

        assert serializer.is_valid()
        product = serializer.save()

        assert product.product_type == 'service'

    def test_profit_margin_read_only(self):
        """Test that profit_margin is read-only."""
        data = {
            'sku': 'TEST-002',
            'name': 'Test',
            'product_type': 'physical',
            'unit_price': '100.00',
            'cost': '50.00',
            'profit_margin': '99.99',  # Try to set manually (should be ignored)
            'is_active': True,
        }
        serializer = ProductSerializer(data=data)

        assert serializer.is_valid()
        product = serializer.save()

        # profit_margin should be computed (50%), not the manually set value
        expected_margin = ((product.unit_price - product.cost) / product.unit_price) * 100
        assert product.profit_margin == expected_margin
        assert product.profit_margin != Decimal('99.99')


@pytest.mark.django_db
class TestSalesTransactionItemSerializer:
    """Tests for SalesTransactionItemSerializer."""

    def test_serialization(self, sales_transaction_item):
        """Test sales transaction item serialization."""
        serializer = SalesTransactionItemSerializer(sales_transaction_item)
        data = serializer.data

        assert data['id'] == sales_transaction_item.id
        assert data['product'] == sales_transaction_item.product.id
        assert 'product_name' in data
        assert data['product_name'] == sales_transaction_item.product.name
        assert 'line_total' in data
        assert 'commission_amount' in data

    def test_product_name_read_only(self, sales_transaction_item):
        """Test that product_name is read-only and computed."""
        serializer = SalesTransactionItemSerializer(sales_transaction_item)
        data = serializer.data

        assert data['product_name'] == sales_transaction_item.product.name

    def test_deserialization(self, sales_transaction, product):
        """Test sales transaction item deserialization."""
        data = {
            'transaction': sales_transaction.id,
            'product': product.id,
            'quantity': 3,
            'unit_price': '99.99',
            'discount_amount': '10.00',
            'commission_rate': '5.00',
        }
        serializer = SalesTransactionItemSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        item = serializer.save()

        assert item.quantity == 3
        assert item.unit_price == Decimal('99.99')
        assert item.discount_amount == Decimal('10.00')

    def test_line_total_computed(self, sales_transaction, product):
        """Test that line_total is computed correctly."""
        data = {
            'transaction': sales_transaction.id,
            'product': product.id,
            'quantity': 2,
            'unit_price': '50.00',
            'discount_amount': '5.00',
            'commission_rate': '0.00',
        }
        serializer = SalesTransactionItemSerializer(data=data)

        assert serializer.is_valid()
        item = serializer.save()

        # line_total = (quantity * unit_price) - discount_amount
        expected_total = (Decimal('2') * Decimal('50.00')) - Decimal('5.00')
        assert item.line_total == expected_total

    def test_commission_amount_computed(self, sales_transaction, product):
        """Test that commission_amount is computed correctly."""
        data = {
            'transaction': sales_transaction.id,
            'product': product.id,
            'quantity': 1,
            'unit_price': '100.00',
            'discount_amount': '0.00',
            'commission_rate': '10.00',
        }
        serializer = SalesTransactionItemSerializer(data=data)

        assert serializer.is_valid()
        item = serializer.save()

        # commission_amount = line_total * (commission_rate / 100)
        expected_commission = item.line_total * (Decimal('10.00') / Decimal('100'))
        assert item.commission_amount == expected_commission


@pytest.mark.django_db
class TestSalesTransactionSerializer:
    """Tests for SalesTransactionSerializer."""

    def test_serialization(self, sales_transaction):
        """Test sales transaction serialization."""
        serializer = SalesTransactionSerializer(sales_transaction)
        data = serializer.data

        assert data['id'] == sales_transaction.id
        assert data['transaction_id'] == sales_transaction.transaction_id
        assert data['customer'] == sales_transaction.customer.id
        assert 'customer_name' in data
        assert 'salesperson_name' in data
        assert 'items' in data
        assert 'total_amount' in data

    def test_customer_name_read_only(self, sales_transaction):
        """Test that customer_name is read-only."""
        serializer = SalesTransactionSerializer(sales_transaction)
        data = serializer.data

        assert data['customer_name'] == sales_transaction.customer.name

    def test_salesperson_name_read_only(self, sales_transaction):
        """Test that salesperson_name is read-only."""
        serializer = SalesTransactionSerializer(sales_transaction)
        data = serializer.data

        assert data['salesperson_name'] == sales_transaction.salesperson.full_name

    def test_deserialization(self, customer, employee):
        """Test sales transaction deserialization."""
        data = {
            'transaction_id': 'TXN-999',
            'customer': customer.id,
            'salesperson': employee.id,
            'transaction_date': '2024-01-15',
            'status': 'completed',
            'payment_method': 'credit_card',
            'subtotal': '200.00',
            'tax_amount': '20.00',
            'discount_amount': '10.00',
            'commission_amount': '10.00',
        }
        serializer = SalesTransactionSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        transaction = serializer.save()

        assert transaction.transaction_id == 'TXN-999'
        assert transaction.status == 'completed'
        assert transaction.payment_method == 'credit_card'

    def test_nested_items_serialization(self, sales_transaction_with_items):
        """Test nested items serialization."""
        serializer = SalesTransactionSerializer(sales_transaction_with_items)
        data = serializer.data

        assert 'items' in data
        assert isinstance(data['items'], list)
        assert len(data['items']) >= 1

        item = data['items'][0]
        assert 'product_name' in item
        assert 'quantity' in item
        assert 'line_total' in item

    def test_items_read_only(self, customer, employee):
        """Test that nested items are read-only."""
        item_data = {
            'product': 1,
            'quantity': 2,
            'unit_price': '50.00',
        }
        data = {
            'transaction_id': 'TXN-888',
            'customer': customer.id,
            'salesperson': employee.id,
            'transaction_date': '2024-01-15',
            'status': 'pending',
            'payment_method': 'cash',
            'subtotal': '100.00',
            'tax_amount': '10.00',
            'discount_amount': '0.00',
            'commission_amount': '5.00',
            'items': [item_data],  # Try to create nested items
        }
        serializer = SalesTransactionSerializer(data=data)

        assert serializer.is_valid()
        transaction = serializer.save()

        # Items should not be created via nested data
        assert transaction.items.count() == 0

    def test_commission_tracking(self, customer, employee):
        """Test commission tracking fields."""
        data = {
            'transaction_id': 'TXN-777',
            'customer': customer.id,
            'salesperson': employee.id,
            'transaction_date': '2024-01-15',
            'status': 'completed',
            'payment_method': 'credit_card',
            'subtotal': '500.00',
            'tax_amount': '50.00',
            'discount_amount': '0.00',
            'commission_amount': '25.00',
            'commission_paid': True,
            'commission_paid_date': '2024-01-20',
        }
        serializer = SalesTransactionSerializer(data=data)

        assert serializer.is_valid()
        transaction = serializer.save()

        assert transaction.commission_paid is True
        assert transaction.commission_paid_date == date(2024, 1, 20)


@pytest.mark.django_db
class TestCommissionPaymentSerializer:
    """Tests for CommissionPaymentSerializer."""

    def test_serialization(self, employee):
        """Test commission payment serialization."""
        payment = CommissionPayment.objects.create(
            employee=employee,
            payment_date=date.today(),
            period_start=date.today() - timedelta(days=30),
            period_end=date.today() - timedelta(days=1),
            total_sales=Decimal('10000.00'),
            commission_amount=Decimal('500.00'),
            status='paid',
        )
        serializer = CommissionPaymentSerializer(payment)
        data = serializer.data

        assert data['id'] == payment.id
        assert data['employee'] == employee.id
        assert 'employee_name' in data
        assert data['employee_name'] == employee.full_name
        assert data['status'] == 'paid'

    def test_employee_name_read_only(self, employee):
        """Test that employee_name is read-only."""
        payment = CommissionPayment.objects.create(
            employee=employee,
            payment_date=date.today(),
            period_start=date.today() - timedelta(days=30),
            period_end=date.today() - timedelta(days=1),
            total_sales=Decimal('5000.00'),
            commission_amount=Decimal('250.00'),
            status='pending',
        )
        serializer = CommissionPaymentSerializer(payment)
        data = serializer.data

        assert data['employee_name'] == employee.full_name

    def test_deserialization(self, employee):
        """Test commission payment deserialization."""
        data = {
            'employee': employee.id,
            'payment_date': '2024-02-01',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'total_sales': '15000.00',
            'commission_amount': '750.00',
            'status': 'paid',
            'notes': 'January commission',
        }
        serializer = CommissionPaymentSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        payment = serializer.save()

        assert payment.employee == employee
        assert payment.total_sales == Decimal('15000.00')
        assert payment.commission_amount == Decimal('750.00')
        assert payment.status == 'paid'

    def test_status_choices(self, employee):
        """Test valid status choices."""
        valid_statuses = ['pending', 'paid', 'cancelled']

        for status_choice in valid_statuses:
            data = {
                'employee': employee.id,
                'payment_date': '2024-02-01',
                'period_start': '2024-01-01',
                'period_end': '2024-01-31',
                'total_sales': '5000.00',
                'commission_amount': '250.00',
                'status': status_choice,
            }
            serializer = CommissionPaymentSerializer(data=data)
            assert serializer.is_valid(), f"Status {status_choice} should be valid"

    def test_period_dates(self, employee):
        """Test commission period dates."""
        data = {
            'employee': employee.id,
            'payment_date': '2024-02-15',
            'period_start': '2024-02-01',
            'period_end': '2024-02-14',
            'total_sales': '8000.00',
            'commission_amount': '400.00',
            'status': 'pending',
        }
        serializer = CommissionPaymentSerializer(data=data)

        assert serializer.is_valid()
        payment = serializer.save()

        assert payment.period_start == date(2024, 2, 1)
        assert payment.period_end == date(2024, 2, 14)
        assert payment.payment_date == date(2024, 2, 15)

    def test_optional_notes(self, employee):
        """Test commission payment with optional notes."""
        data = {
            'employee': employee.id,
            'payment_date': '2024-02-01',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'total_sales': '5000.00',
            'commission_amount': '250.00',
            'status': 'paid',
        }
        serializer = CommissionPaymentSerializer(data=data)

        assert serializer.is_valid()
        payment = serializer.save()

        assert payment.notes is None or payment.notes == ''
