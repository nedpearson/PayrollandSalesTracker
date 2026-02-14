"""
ASGI config for payroll_sales_tracker project.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payroll_sales_tracker.settings')

application = get_asgi_application()
