"""URL configuration for sales app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, ProductViewSet, SalesTransactionViewSet,
    SalesTransactionItemViewSet, CommissionPaymentViewSet
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'products', ProductViewSet)
router.register(r'transactions', SalesTransactionViewSet)
router.register(r'transaction-items', SalesTransactionItemViewSet)
router.register(r'commission-payments', CommissionPaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
