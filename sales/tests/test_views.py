"""API endpoint tests for sales app."""
import pytest
from rest_framework.test import APIClient
from rest_framework import status


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_sales_client(sales_employee):
    """Create authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=sales_employee.user)
    return client


@pytest.mark.integration
class TestSalesAPI:
    """Tests for Sales API endpoints."""

    def test_list_products(self, authenticated_sales_client, product):
        """Test listing products."""
        url = '/api/sales/products/'
        response = authenticated_sales_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_retrieve_product(self, authenticated_sales_client, product):
        """Test retrieving a specific product."""
        url = f'/api/sales/products/{product.id}/'
        response = authenticated_sales_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['sku'] == 'PROD001'
        assert 'profit_margin' in response.data

    def test_list_transactions(self, authenticated_sales_client, sales_transaction):
        """Test listing sales transactions."""
        url = '/api/sales/transactions/'
        response = authenticated_sales_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_filter_transactions_by_status(self, authenticated_sales_client, sales_transaction):
        """Test filtering transactions by status."""
        url = '/api/sales/transactions/?status=COMPLETED'
        response = authenticated_sales_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for result in response.data['results']:
            assert result['status'] == 'COMPLETED'

    def test_unauthorized_access(self, api_client):
        """Test that unauthenticated users cannot access sales data."""
        url = '/api/sales/transactions/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
