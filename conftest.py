"""Root conftest.py for shared pytest configuration and fixtures."""
import pytest
import os
import django
from django.conf import settings


# Configure Django settings for pytest
def pytest_configure():
    """Configure Django settings for testing."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payroll_sales_tracker.settings')
    django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up test database."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
