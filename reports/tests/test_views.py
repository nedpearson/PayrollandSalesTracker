"""Tests for reports API endpoints."""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User


@pytest.fixture
def report_user(db):
    """Create a user for reports testing."""
    return User.objects.create_user(
        username='report_user',
        password='testpass'
    )


@pytest.fixture
def authenticated_report_client(report_user):
    """Create authenticated API client for reports."""
    client = APIClient()
    client.force_authenticate(user=report_user)
    return client


@pytest.mark.integration
class TestReportsAPI:
    """Tests for Reports API endpoints."""

    def test_employee_summary_report(self, authenticated_report_client, employee):
        """Test employee summary report."""
        url = '/api/reports/employee-summary/'
        response = authenticated_report_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total_employees' in response.data
        assert 'active_employees' in response.data
        assert 'by_department' in response.data

    def test_payroll_summary_report(self, authenticated_report_client, paycheck):
        """Test payroll summary report."""
        url = f'/api/reports/payroll-summary/?period_id={paycheck.payroll_period.id}'
        response = authenticated_report_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total_gross_pay' in response.data
        assert 'total_net_pay' in response.data

    def test_sales_summary_report(self, authenticated_report_client, sales_transaction):
        """Test sales summary report."""
        url = '/api/reports/sales-summary/'
        response = authenticated_report_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total_sales' in response.data
        assert 'total_transactions' in response.data
