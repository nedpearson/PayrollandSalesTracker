"""Fixtures for sales tests."""
import pytest
from decimal import Decimal
from datetime import datetime
from django.contrib.auth.models import User
from employees.models import Department, Employee
from sales.models import Customer, Product, SalesTransaction, SalesTransactionItem


@pytest.fixture
def sales_employee(db):
    """Create a sales employee."""
    user = User.objects.create_user(username='sales_rep')
    dept = Department.objects.create(name='Sales', code='SALES')
    from datetime import date
    return Employee.objects.create(
        user=user,
        employee_id='SALES001',
        first_name='Bob',
        last_name='Sales',
        email='bob@example.com',
        date_of_birth=date(1988, 3, 10),
        ssn_last_four='9999',
        department=dept,
        job_title='Sales Rep',
        employment_type='FULL_TIME',
        employment_status='ACTIVE',
        hire_date=date(2018, 1, 1),
        base_salary=Decimal('50000.00'),
        pay_frequency='BI_WEEKLY',
    )


@pytest.fixture
def customer(db):
    """Create a test customer."""
    return Customer.objects.create(
        customer_id='CUST001',
        name='Acme Corporation',
        customer_type='BUSINESS',
        email='contact@acme.com',
        phone='555-9999',
        company='Acme Corp',
        is_active=True,
    )


@pytest.fixture
def product(db):
    """Create a test product."""
    return Product.objects.create(
        sku='PROD001',
        name='Widget Pro',
        description='Premium widget',
        product_type='PRODUCT',
        unit_price=Decimal('99.99'),
        cost=Decimal('50.00'),
        commission_rate=Decimal('10.00'),
        is_taxable=True,
        is_active=True,
    )


@pytest.fixture
def sales_transaction(db, customer, sales_employee):
    """Create a sales transaction."""
    return SalesTransaction.objects.create(
        transaction_id='TXN001',
        customer=customer,
        salesperson=sales_employee,
        transaction_date=datetime(2024, 1, 15, 10, 30),
        status='COMPLETED',
        payment_method='CREDIT_CARD',
        subtotal=Decimal('199.98'),
        tax_amount=Decimal('13.00'),
        discount_amount=Decimal('0.00'),
    )


@pytest.fixture
def transaction_item(db, sales_transaction, product):
    """Create a transaction item."""
    return SalesTransactionItem.objects.create(
        transaction=sales_transaction,
        product=product,
        quantity=Decimal('2.00'),
        unit_price=Decimal('99.99'),
        commission_rate=Decimal('10.00'),
    )
