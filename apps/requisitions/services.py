"""
Services for requisitions app
"""
import logging
from typing import Dict, Any, Optional, List
from django.db.models import Q, QuerySet, Count, Sum, Case, When, IntegerField
from django.db import transaction
from django.utils import timezone
from django.db.models.functions import TruncMonth

from apps.core.services.base import BaseService, ValidationServiceException
from apps.requisitions.models import ExtractionRequest
from apps.core.models import ExtractionUnit
from apps.base_tables.models import AgencyUnit


class ExtractionRequestService(BaseService):
    """Service for ExtractionRequest business logic"""
    
    model_class = ExtractionRequest
    
    def get_queryset(self) -> QuerySet:
        """Get extraction requests queryset with optimized queries"""
        queryset = super().get_queryset().select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category',
            'created_by',
            'received_by',
            'case'
        ).order_by('-requested_at', '-created_at')
        
        # Aplica filtro de extraction_unit para usuários extratores
        queryset = self._apply_extraction_unit_filter(queryset)
        
        return queryset
    
    def _apply_extraction_unit_filter(self, queryset: QuerySet) -> QuerySet:
        """
        Filtra queryset baseado nas extraction_units do usuário extrator.
        Superusuários veem todos os dados.
        """
        if not self.user or self.user.is_superuser:
            return queryset
        
        try:
            from apps.core.models import ExtractorUser
            
            # Busca todos os ExtractorUser vinculados ao usuário
            extractor_users = ExtractorUser.objects.filter(
                user=self.user,
                deleted_at__isnull=True
            ).prefetch_related('extraction_unit_extractors')
            
            if not extractor_users.exists():
                # Não é um extrator, retorna queryset completo
                return queryset
            
            # Obtém todas as extraction_units vinculadas aos extractors do usuário
            extraction_unit_ids = []
            for extractor in extractor_users:
                unit_ids = extractor.extraction_unit_extractors.filter(
                    deleted_at__isnull=True
                ).values_list('extraction_unit_id', flat=True)
                extraction_unit_ids.extend(unit_ids)
            
            if not extraction_unit_ids:
                # Extrator sem unidades vinculadas
                return queryset.none()
            
            # Filtra pelo campo extraction_unit
            return queryset.filter(extraction_unit__in=extraction_unit_ids)
            
        except Exception:
            # Em caso de erro, retorna queryset completo
            return queryset
    
    def apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply filters to queryset"""
        search = filters.get('search')
        if search:
            queryset = queryset.filter(
                Q(request_procedures__icontains=search) |
                Q(requester_authority_name__icontains=search) |
                Q(additional_info__icontains=search) |
                Q(requester_agency_unit__name__icontains=search) |
                Q(requester_agency_unit__acronym__icontains=search)
            )
        
        status = filters.get('status')
        if status:
            # status pode ser uma lista
            if isinstance(status, list):
                queryset = queryset.filter(status__in=status)
            else:
                queryset = queryset.filter(status=status)
        
        extraction_unit = filters.get('extraction_unit')
        if extraction_unit:
            # extraction_unit pode ser:
            # - model instance
            # - lista/tupla de instances/ids
            # - QuerySet (ModelMultipleChoiceField)
            if isinstance(extraction_unit, (list, tuple, set)):
                queryset = queryset.filter(extraction_unit__in=extraction_unit)
            elif hasattr(extraction_unit, 'values_list'):
                queryset = queryset.filter(extraction_unit__in=extraction_unit.values_list('pk', flat=True))
            else:
                queryset = queryset.filter(extraction_unit=extraction_unit)
        
        crime_category = filters.get('crime_category')
        if crime_category:
            queryset = queryset.filter(crime_category=crime_category)
        
        date_from = filters.get('date_from')
        if date_from:
            queryset = queryset.filter(requested_at__date__gte=date_from)
        
        date_to = filters.get('date_to')
        if date_to:
            queryset = queryset.filter(requested_at__date__lte=date_to)
        
        return queryset
    
    def get_not_received(self) -> QuerySet:
        """Get extraction requests that are not received"""
        return self.get_queryset().filter(
            received_at__isnull=True,
            status__in=[
                ExtractionRequest.REQUEST_STATUS_PENDING,
                ExtractionRequest.REQUEST_STATUS_ASSIGNED
            ]
        )
    
    @transaction.atomic
    def create_case_from_request(self, request_pk: int, receipt_notes: str = None) -> 'Case':
        """
        Cria um Case a partir de um ExtractionRequest e marca o request como recebido.
        Operação atômica: criação do Case e atualização do ExtractionRequest são executadas
        em uma única transação. Se falharem, tudo será revertido.
        
        Args:
            request_pk: ID da ExtractionRequest
            receipt_notes: Observações sobre o recebimento do material (opcional)
        
        Nota: Falhas no parsing de procedimentos (CaseProcedure) não impedem a criação do case.
        
        Este método delega a criação do case para o CaseService, mantendo apenas
        a responsabilidade de buscar o ExtractionRequest e marcar como recebido.
        """
        from apps.cases.services.case_service import CaseService
        
        extraction_request = self.get_object(request_pk)
        
        # Delega a criação do case para o CaseService
        # O CaseService já faz: criar case, parsear procedimentos, e opcionalmente marcar request como recebido
        case_service = CaseService(user=self.user)
        case = case_service.create_case_from_requisition(
            requisition=extraction_request,
            user=self.user,
            mark_request_as_received=True,
            receipt_notes=receipt_notes
        )
        
        return case
    


# Funções auxiliares mantidas para compatibilidade
def apply_filters_to_queryset(queryset, filters):
    """Apply filters to ExtractionRequest queryset - mantida para compatibilidade"""
    service = ExtractionRequestService()
    return service.apply_filters(queryset, filters)


def list_extraction_units(user=None):
    """
    List extraction units for selects/filters.

    - Superuser e não-extratores: todas as unidades ativas
    - Extratores: apenas unidades associadas (pode ser vazio)
    """
    queryset = ExtractionUnit.objects.filter(deleted_at__isnull=True).order_by('acronym', 'name')

    if not user or getattr(user, 'is_superuser', False):
        return queryset

    service = BaseService(user=user)
    if service.is_extractor_user():
        extraction_unit_ids = service.get_user_extraction_units()
        return queryset.filter(id__in=extraction_unit_ids)

    return queryset


def list_agency_units():
    """List all active agency units"""
    return AgencyUnit.objects.filter(deleted_at__isnull=True).order_by('acronym', 'name')


def get_distribution_summary():
    """
    Get distribution summary for extraction requests by unit.
    Returns data in format expected by extraction_request_form.html template.
    """
    queryset = ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    summary_data = []
    
    # Get all active extraction units
    all_units = ExtractionUnit.objects.filter(deleted_at__isnull=True).order_by('acronym', 'name')
    
    # Get aggregated data for units that have requests
    units_data_dict = {}
    units_with_requests = queryset.exclude(
        extraction_unit__isnull=True
    ).values('extraction_unit').annotate(
        total_requests=Count('id'),
        total_devices=Sum('requested_device_amount'),
        pending_requests=Count(
            Case(
                When(
                    status__in=[
                        ExtractionRequest.REQUEST_STATUS_PENDING,
                        ExtractionRequest.REQUEST_STATUS_ASSIGNED
                    ],
                    then=1
                ),
                output_field=IntegerField()
            )
        ),
        in_progress_requests=Count(
            Case(
                When(
                    status__in=[
                        ExtractionRequest.REQUEST_STATUS_IN_PROGRESS,
                        ExtractionRequest.REQUEST_STATUS_WAITING_START
                    ],
                    then=1
                ),
                output_field=IntegerField()
            )
        ),
        received_requests=Count(
            Case(
                When(
                    status=ExtractionRequest.REQUEST_STATUS_RECEIVED,
                    then=1
                ),
                output_field=IntegerField()
            )
        )
    )
    
    # Create a dictionary for quick lookup
    for unit_data in units_with_requests:
        unit_id = unit_data['extraction_unit']
        if unit_id:
            units_data_dict[unit_id] = unit_data
    
    # Process all units (including those without requests)
    for unit in all_units:
        unit_id = unit.pk
        unit_requests = queryset.filter(extraction_unit_id=unit_id)
        
        # Get data from dictionary or use defaults
        if unit_id in units_data_dict:
            unit_data = units_data_dict[unit_id]
            total_requests = unit_data['total_requests']
            total_devices = unit_data['total_devices'] or 0
            pending_requests = unit_data['pending_requests']
            in_progress_requests = unit_data['in_progress_requests']
            received_requests = unit_data['received_requests']
        else:
            # Unit has no requests - use zero values
            total_requests = 0
            total_devices = 0
            pending_requests = 0
            in_progress_requests = 0
            received_requests = 0
        
        # Calculate pending devices (from pending/assigned requests)
        pending_devices = unit_requests.filter(
            status__in=[
                ExtractionRequest.REQUEST_STATUS_PENDING,
                ExtractionRequest.REQUEST_STATUS_ASSIGNED
            ]
        ).aggregate(
            total=Sum('requested_device_amount')
        )['total'] or 0
        
        # Determine if unit is overloaded or available
        is_overloaded = pending_devices > 50 or pending_requests > 30
        is_available = pending_devices < 10 and pending_requests < 5
        
        summary_data.append({
            'unit': unit,
            'total_requests': total_requests,
            'total_devices': total_devices,
            'pending_requests': pending_requests,
            'in_progress_requests': in_progress_requests,
            'received_requests': received_requests,
            'pending_devices': pending_devices,
            'is_overloaded': is_overloaded,
            'is_available': is_available
        })
    
    # Sort by total requests (descending), then by unit name
    summary_data.sort(key=lambda x: (x['total_requests'], x['unit'].acronym or x['unit'].name), reverse=True)
    
    return summary_data


def get_distribution_report(filters=None):
    """
    Generate distribution report data
    
    Args:
        filters: Dict with filter parameters
    
    Returns:
        Dict with report data
    """
    if filters is None:
        filters = {}
    
    # Convert filter names for compatibility with apply_filters
    normalized_filters = filters.copy()
    if 'start_date' in normalized_filters:
        normalized_filters['date_from'] = normalized_filters.pop('start_date')
    if 'end_date' in normalized_filters:
        normalized_filters['date_to'] = normalized_filters.pop('end_date')
    
    # Handle year filter
    if 'year' in normalized_filters and 'date_from' not in normalized_filters and 'date_to' not in normalized_filters:
        year = normalized_filters.pop('year')
        normalized_filters['date_from'] = timezone.datetime(year, 1, 1).date()
        normalized_filters['date_to'] = timezone.datetime(year, 12, 31).date()
    
    # Base queryset
    queryset = ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    # Apply filters
    service = ExtractionRequestService()
    queryset = service.apply_filters(queryset, normalized_filters)
    
    # Summary by unit - Include all extraction units, even without requests
    summary_by_unit = []
    
    # Get all active extraction units
    all_units = ExtractionUnit.objects.filter(deleted_at__isnull=True).order_by('acronym', 'name')
    
    # If there's an extraction_unit filter, apply it to the units list
    extraction_unit_filter = filters.get('extraction_unit')
    if extraction_unit_filter:
        if isinstance(extraction_unit_filter, list):
            all_units = all_units.filter(id__in=extraction_unit_filter)
        else:
            all_units = all_units.filter(id=extraction_unit_filter)
    
    # Get aggregated data for units that have requests
    units_data_dict = {}
    units_with_requests = queryset.exclude(
        extraction_unit__isnull=True
    ).values('extraction_unit').annotate(
        total_requests=Count('id'),
        total_devices=Sum('requested_device_amount')
    )
    
    # Create a dictionary for quick lookup
    for unit_data in units_with_requests:
        unit_id = unit_data['extraction_unit']
        if unit_id:
            units_data_dict[unit_id] = unit_data
    
    # Process all units (including those without requests)
    for unit in all_units:
        unit_id = unit.id
        unit_requests = queryset.filter(extraction_unit_id=unit_id)
        
        # Get data from dictionary if unit has requests, otherwise use zeros
        if unit_id in units_data_dict:
            unit_data = units_data_dict[unit_id]
            total_requests = unit_data['total_requests']
            total_devices = unit_data['total_devices'] or 0
        else:
            total_requests = 0
            total_devices = 0
        
        # Calculate efficiency score
        completed = unit_requests.filter(
            status__in=['waiting_collect', 'in_progress']
        ).count()
        efficiency_score = (completed / total_requests * 100) if total_requests > 0 else 0
        
        summary_by_unit.append({
            'unit': unit,
            'total_requests': total_requests,
            'total_devices': total_devices,
            'efficiency_score': round(efficiency_score, 2)
        })
    
    # Sort by total_requests (descending) to maintain the original behavior
    summary_by_unit.sort(key=lambda x: x['total_requests'], reverse=True)
    
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
    
    distribution_efficiency = {
        'completion_rate': round(completion_rate, 2),
        'avg_processing_time_days': 0,  # Can be improved
        'efficiency_score': round(completion_rate, 2)
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
