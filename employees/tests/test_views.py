"""API endpoint tests for employees app."""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from employees.models import Employee, Department


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(user):
    """Create authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.integration
class TestEmployeeAPI:
    """Tests for Employee API endpoints."""

    def test_list_employees_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list employees."""
        url = '/api/employees/employees/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_employees_authenticated(self, authenticated_client, employee):
        """Test listing employees with authentication."""
        url = '/api/employees/employees/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_retrieve_employee(self, authenticated_client, employee):
        """Test retrieving a specific employee."""
        url = f'/api/employees/employees/{employee.id}/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['employee_id'] == 'EMP001'
        assert response.data['full_name'] == 'John Doe'

    def test_filter_employees_by_status(self, authenticated_client, employee):
        """Test filtering employees by status."""
        url = '/api/employees/employees/?employment_status=ACTIVE'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_search_employees(self, authenticated_client, employee):
        """Test searching employees by name."""
        url = '/api/employees/employees/?search=John'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1


@pytest.mark.integration
class TestDepartmentAPI:
    """Tests for Department API endpoints."""

    def test_list_departments(self, authenticated_client, department):
        """Test listing departments."""
        url = '/api/employees/departments/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_retrieve_department(self, authenticated_client, department):
        """Test retrieving a specific department."""
        url = f'/api/employees/departments/{department.id}/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Engineering'
        assert response.data['code'] == 'ENG'
