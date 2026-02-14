"""Sales models for tracking transactions and commissions."""
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from employees.models import Employee


class Customer(models.Model):
    """Customer model."""

    CUSTOMER_TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('BUSINESS', 'Business'),
    ]

    customer_id = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=20, blank=True, help_text="EIN or SSN")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.customer_id} - {self.name}"


class Product(models.Model):
    """Product/Service model."""

    PRODUCT_TYPE_CHOICES = [
        ('PRODUCT', 'Product'),
        ('SERVICE', 'Service'),
    ]

    sku = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Commission percentage",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.unit_price > 0:
            return ((self.unit_price - self.cost) / self.unit_price) * 100
        return Decimal('0.00')


class SalesTransaction(models.Model):
    """Sales transaction model."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('REFUNDED', 'Refunded'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('CHECK', 'Check'),
        ('WIRE_TRANSFER', 'Wire Transfer'),
        ('OTHER', 'Other'),
    ]

    transaction_id = models.CharField(max_length=50, unique=True, db_index=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    salesperson = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='sales_transactions'
    )
    transaction_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)

    # Amounts
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Commission
    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    commission_paid = models.BooleanField(default=False)
    commission_paid_date = models.DateField(null=True, blank=True)

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_date', 'status']),
            models.Index(fields=['salesperson', 'transaction_date']),
            models.Index(fields=['customer', 'transaction_date']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.customer.name}"

    def calculate_total(self):
        """Calculate total amount."""
        return self.subtotal + self.tax_amount - self.discount_amount

    def calculate_commission(self):
        """Calculate commission based on line items."""
        total_commission = Decimal('0.00')
        for item in self.items.all():
            total_commission += item.commission_amount
        return total_commission

    def save(self, *args, **kwargs):
        """Override save to calculate totals."""
        self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)


class SalesTransactionItem(models.Model):
    """Line items for sales transactions."""

    transaction = models.ForeignKey(
        SalesTransaction,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='transaction_items'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Commission percentage for this item"
    )
    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['transaction', 'id']

    def __str__(self):
        return f"{self.transaction.transaction_id} - {self.product.name}"

    def calculate_line_total(self):
        """Calculate line total."""
        return (self.quantity * self.unit_price) - self.discount_amount

    def calculate_commission(self):
        """Calculate commission for this line item."""
        return self.line_total * (self.commission_rate / Decimal('100'))

    def save(self, *args, **kwargs):
        """Override save to calculate totals."""
        self.line_total = self.calculate_line_total()
        self.commission_amount = self.calculate_commission()
        super().save(*args, **kwargs)


class CommissionPayment(models.Model):
    """Commission payment tracking."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='commission_payments'
    )
    payment_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    total_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('PAID', 'Paid'),
        ],
        default='PENDING'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['employee', 'payment_date']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.payment_date}"
