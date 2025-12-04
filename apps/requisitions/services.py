"""
Service functions for extraction requests
"""
from django.db.models import Q, Count, Sum, Avg, Case, When, IntegerField, F
from django.utils import timezone
from datetime import datetime, timedelta
from apps.requisitions.models import ExtractionRequest
from apps.core.models import ExtractionUnit
from apps.base_tables.models import AgencyUnit


def apply_filters_to_queryset(queryset, filters):
    """
    Apply filters to ExtractionRequest queryset
    
    Args:
        queryset: Base queryset
        filters: Dict with filter parameters:
            - year: int
            - start_date: date
            - end_date: date
            - extraction_unit: int (pk)
            - status: str
            - requester_agency_unit: int (pk)
    
    Returns:
        Filtered queryset
    """
    if filters.get('year'):
        queryset = queryset.filter(requested_at__year=filters['year'])
    
    if filters.get('start_date'):
        queryset = queryset.filter(requested_at__date__gte=filters['start_date'])
    
    if filters.get('end_date'):
        queryset = queryset.filter(requested_at__date__lte=filters['end_date'])
    
    if filters.get('extraction_unit'):
        queryset = queryset.filter(extraction_unit_id=filters['extraction_unit'])
    
    if filters.get('status'):
        queryset = queryset.filter(status=filters['status'])
    
    if filters.get('requester_agency_unit'):
        queryset = queryset.filter(requester_agency_unit_id=filters['requester_agency_unit'])
    
    return queryset


def list_extraction_units():
    """List all active extraction units"""
    return ExtractionUnit.objects.filter(deleted_at__isnull=True).order_by('acronym', 'name')


def list_agency_units():
    """List all active agency units"""
    return AgencyUnit.objects.filter(deleted_at__isnull=True).order_by('acronym', 'name')


def get_distribution_report(filters=None):
    """
    Generate distribution report data
    
    Args:
        filters: Dict with filter parameters
    
    Returns:
        Dict with report data including:
            - summary_by_unit: List of dicts with unit statistics
            - summary_by_status: List of dicts with status statistics
            - summary_by_month: List of dicts with monthly statistics
            - top_requesting_units: List of top requesting units
            - distribution_efficiency: Dict with efficiency metrics
            - chart_data: Dict with chart data
            - statistics: Dict with general statistics
    """
    if filters is None:
        filters = {}
    
    # Base queryset
    queryset = ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    # Apply filters
    queryset = apply_filters_to_queryset(queryset, filters)
    
    # Summary by unit
    summary_by_unit = []
    units_data = queryset.values('extraction_unit').annotate(
        total_requests=Count('id'),
        total_devices=Sum('requested_device_amount')
    ).order_by('-total_requests')
    
    for unit_data in units_data:
        unit_id = unit_data['extraction_unit']
        if unit_id:
            try:
                unit = ExtractionUnit.objects.get(pk=unit_id)
                unit_requests = queryset.filter(extraction_unit_id=unit_id)
                
                # Calculate efficiency score (simplified - can be improved)
                completed = unit_requests.filter(
                    status__in=['waiting_collect', 'in_progress']
                ).count()
                total = unit_data['total_requests']
                efficiency_score = (completed / total * 100) if total > 0 else 0
                
                summary_by_unit.append({
                    'unit': unit,
                    'total_requests': unit_data['total_requests'],
                    'total_devices': unit_data['total_devices'] or 0,
                    'efficiency_score': round(efficiency_score, 2)
                })
            except ExtractionUnit.DoesNotExist:
                continue
    
    # Summary by status
    summary_by_status = []
    status_data = queryset.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for status_item in status_data:
        status_code = status_item['status']
        summary_by_status.append({
            'status': status_code,
            'count': status_item['count']
        })
    
    # Summary by month
    summary_by_month = []
    from django.db.models.functions import TruncMonth
    monthly_data = queryset.filter(
        requested_at__isnull=False
    ).annotate(
        month=TruncMonth('requested_at')
    ).values('month').annotate(
        count=Count('id'),
        devices=Sum('requested_device_amount')
    ).order_by('month')
    
    for month_item in monthly_data:
        summary_by_month.append({
            'month': month_item['month'],
            'count': month_item['count'],
            'devices': month_item['devices'] or 0
        })
    
    # Top requesting units
    top_requesting_units = []
    requester_data = queryset.values(
        'requester_agency_unit__id',
        'requester_agency_unit__name',
        'requester_agency_unit__acronym'
    ).annotate(
        request_count=Count('id')
    ).order_by('-request_count')[:10]
    
    for requester_item in requester_data:
        top_requesting_units.append({
            'requester_agency_unit__id': requester_item['requester_agency_unit__id'],
            'requester_agency_unit__name': requester_item['requester_agency_unit__name'],
            'requester_agency_unit__acronym': requester_item['requester_agency_unit__acronym'],
            'request_count': requester_item['request_count']
        })
    
    # Distribution efficiency
    total_requests = queryset.count()
    completed_requests = queryset.filter(
        status__in=['waiting_collect', 'in_progress']
    ).count()
    completion_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
    
    # Calculate average processing time (simplified)
    avg_processing_time_days = 0  # Can be improved with actual processing time calculation
    
    distribution_efficiency = {
        'completion_rate': round(completion_rate, 2),
        'avg_processing_time_days': round(avg_processing_time_days, 2),
        'efficiency_score': round(completion_rate, 2)  # Simplified
    }
    
    # Chart data
    chart_data = {
        'unit_distribution': [
            {
                'extraction_unit__id': item['unit'].id,
                'extraction_unit__name': item['unit'].name,
                'extraction_unit__acronym': item['unit'].acronym,
                'count': item['total_requests']
            }
            for item in summary_by_unit
        ],
        'unit_devices_distribution': [
            {
                'extraction_unit__id': item['unit'].id,
                'extraction_unit__name': item['unit'].name,
                'extraction_unit__acronym': item['unit'].acronym,
                'devices': item['total_devices']
            }
            for item in summary_by_unit
        ],
        'status_distribution': [
            {
                'status': item['status'],
                'count': item['count']
            }
            for item in summary_by_status
        ],
        'monthly_trend': [
            {
                'month': item['month'].strftime('%Y-%m') if item['month'] else '',
                'count': item['count'],
                'devices': item['devices']
            }
            for item in summary_by_month
        ],
        'top_requesting_units': top_requesting_units
    }
    
    # Statistics
    total_devices = queryset.aggregate(
        total=Sum('requested_device_amount')
    )['total'] or 0
    
    avg_devices_per_request = (total_devices / total_requests) if total_requests > 0 else 0
    
    # Date range
    date_range = {}
    if queryset.exists():
        first_request = queryset.order_by('requested_at').first()
        last_request = queryset.order_by('-requested_at').first()
        if first_request and last_request and first_request.requested_at and last_request.requested_at:
            date_range = {
                'start_date': first_request.requested_at.date(),
                'end_date': last_request.requested_at.date()
            }
    
    unique_units = queryset.exclude(extraction_unit__isnull=True).values('extraction_unit').distinct().count()
    unique_requesters = queryset.exclude(requester_agency_unit__isnull=True).values('requester_agency_unit').distinct().count()
    
    statistics = {
        'total_requests': total_requests,
        'total_devices': total_devices,
        'avg_devices_per_request': round(avg_devices_per_request, 2),
        'date_range': date_range,
        'unique_units': unique_units,
        'unique_requesters': unique_requesters
    }
    
    return {
        'filters_applied': filters,
        'total_requests': total_requests,
        'summary_by_unit': summary_by_unit,
        'summary_by_status': summary_by_status,
        'summary_by_month': summary_by_month,
        'top_requesting_units': top_requesting_units,
        'distribution_efficiency': distribution_efficiency,
        'chart_data': chart_data,
        'statistics': statistics
    }

