"""Views for reports app."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from employees.models import Employee
from payroll.models import Paycheck, PayrollPeriod
from sales.models import SalesTransaction


class PayrollSummaryReport(APIView):
    """Summary report for payroll data."""

    def get(self, request):
        """Get payroll summary statistics."""
        period_id = request.query_params.get('period_id')

        if period_id:
            paychecks = Paycheck.objects.filter(payroll_period_id=period_id)
        else:
            # Default to latest period
            latest_period = PayrollPeriod.objects.first()
            if not latest_period:
                return Response(
                    {'error': 'No payroll periods found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            paychecks = Paycheck.objects.filter(payroll_period=latest_period)

        summary = paychecks.aggregate(
            total_gross_pay=Sum('gross_pay'),
            total_net_pay=Sum('net_pay'),
            total_taxes=Sum('federal_income_tax') + Sum('state_income_tax') +
                       Sum('social_security_tax') + Sum('medicare_tax'),
            employee_count=Count('id'),
            avg_gross_pay=Avg('gross_pay'),
        )

        return Response(summary)


class SalesSummaryReport(APIView):
    """Summary report for sales data."""

    def get(self, request):
        """Get sales summary statistics."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        transactions = SalesTransaction.objects.filter(status='COMPLETED')

        if start_date:
            transactions = transactions.filter(transaction_date__gte=start_date)
        if end_date:
            transactions = transactions.filter(transaction_date__lte=end_date)

        if not start_date and not end_date:
            # Default to last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            transactions = transactions.filter(transaction_date__gte=thirty_days_ago)

        summary = transactions.aggregate(
            total_sales=Sum('total_amount'),
            total_transactions=Count('id'),
            total_commission=Sum('commission_amount'),
            avg_transaction=Avg('total_amount'),
        )

        # Top salespeople
        top_salespeople = (
            transactions.values('salesperson__first_name', 'salesperson__last_name')
            .annotate(total_sales=Sum('total_amount'), transaction_count=Count('id'))
            .order_by('-total_sales')[:10]
        )

        summary['top_salespeople'] = list(top_salespeople)

        return Response(summary)


class EmployeeSummaryReport(APIView):
    """Summary report for employee data."""

    def get(self, request):
        """Get employee summary statistics."""
        summary = {
            'total_employees': Employee.objects.count(),
            'active_employees': Employee.objects.filter(employment_status='ACTIVE').count(),
            'by_department': list(
                Employee.objects.values('department__name')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            'by_employment_type': list(
                Employee.objects.values('employment_type')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            'by_status': list(
                Employee.objects.values('employment_status')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
        }

        return Response(summary)
