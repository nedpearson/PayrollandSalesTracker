"""
WSGI config for payroll_sales_tracker project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payroll_sales_tracker.settings')

application = get_wsgi_application()
