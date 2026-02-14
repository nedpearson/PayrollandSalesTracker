"""URL configuration for payroll app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PayrollPeriodViewSet, PaycheckViewSet, TaxRateViewSet,
    DeductionViewSet, EmployeeDeductionViewSet
)

router = DefaultRouter()
router.register(r'periods', PayrollPeriodViewSet)
router.register(r'paychecks', PaycheckViewSet)
router.register(r'tax-rates', TaxRateViewSet)
router.register(r'deductions', DeductionViewSet)
router.register(r'employee-deductions', EmployeeDeductionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
