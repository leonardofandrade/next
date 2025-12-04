"""
Views for distribution analysis and reporting
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

from apps.core.models import ExtractionUnit, ExtractionAgency, ReportsSettings
from apps.requisitions.models import ExtractionRequest
from apps.requisitions.services import (
    get_distribution_report,
    apply_filters_to_queryset,
    list_extraction_units,
    list_agency_units
)
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.conf import settings


class DistributionReportView(LoginRequiredMixin, TemplateView):
    """View for distribution analysis report"""
    
    template_name = 'requisitions/distribution_report.html'
    
    def get_context_data(self, **kwargs):
        """Get context data for the report"""
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters from request
        filters = self._get_filters_from_request()
        
        # Always show results (with or without filters)
        show_results = True

        # Get report data
        try:
            report_data = get_distribution_report(filters)
            
            # Handle pagination and ordering for requests list
            requests_queryset = self._get_requests_queryset(filters)
            paginator = Paginator(requests_queryset, settings.PAGINATE_BY)
            page_number = self.request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Update report_data with paginated requests
            requests_data = []
            for request_obj in page_obj.object_list:
                request_data = {
                    'id': request_obj.id,
                    'status': request_obj.status,
                    'requested_device_amount': request_obj.requested_device_amount,
                    'requested_at': request_obj.requested_at,
                    'request_procedures': request_obj.request_procedures,
                    'requester_agency_unit__name': request_obj.requester_agency_unit.name if request_obj.requester_agency_unit else '',
                    'requester_agency_unit__acronym': request_obj.requester_agency_unit.acronym if request_obj.requester_agency_unit else '',
                    'extraction_unit__name': request_obj.extraction_unit.name if request_obj.extraction_unit else '',
                    'extraction_unit__acronym': request_obj.extraction_unit.acronym if request_obj.extraction_unit else '',
                    'get_status_display': request_obj.get_status_display(),
                    'get_status_color': request_obj.get_status_color()
                }
                requests_data.append(request_data)
            
            report_data['requests_list'] = requests_data
            report_data['page_obj'] = page_obj
            report_data['is_paginated'] = page_obj.has_other_pages()
            
        except Exception as e:
            messages.error(self.request, f'Erro ao gerar relatório: {str(e)}')
            report_data = self._empty_report(filters)
        
        # Prepare chart data JSON (serialize datetimes safely)
        try:
            chart_data_json = json.dumps(report_data.get('chart_data', {}), cls=DjangoJSONEncoder)
        except Exception:
            chart_data_json = json.dumps({'unit_distribution': [], 'status_distribution': [], 'monthly_trend': []})

        # Page information
        context.update({
            'page_title': 'Extrato de Distribuições',
            'page_title_icon': 'fas fa-chart-line',
            'page_description': 'Análise completa das distribuições de solicitações por unidade de extração',
            'report_data': report_data,
            'filters': filters,
            'filter_options': self._get_filter_options(),
            'show_results': show_results,
            'chart_data_json': chart_data_json
        })
        
        return context
    
    def _get_filters_from_request(self):
        """Extract filters from request parameters"""
        filters = {}
        
        # Year filter
        if self.request.GET.get('year'):
            try:
                filters['year'] = int(self.request.GET.get('year'))
            except ValueError:
                pass
        
        # Date range filters
        if self.request.GET.get('start_date'):
            try:
                filters['start_date'] = datetime.strptime(
                    self.request.GET.get('start_date'), '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        
        if self.request.GET.get('end_date'):
            try:
                filters['end_date'] = datetime.strptime(
                    self.request.GET.get('end_date'), '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        
        # Extraction unit filter
        if self.request.GET.get('extraction_unit'):
            try:
                filters['extraction_unit'] = int(self.request.GET.get('extraction_unit'))
            except ValueError:
                pass
        
        # Status filter
        if self.request.GET.get('status'):
            filters['status'] = self.request.GET.get('status')
        
        # Requester agency unit filter
        if self.request.GET.get('requester_agency_unit'):
            try:
                filters['requester_agency_unit'] = int(self.request.GET.get('requester_agency_unit'))
            except ValueError:
                pass
        
        return filters
    
    def _get_requests_queryset(self, filters):
        """Get queryset for requests list with ordering"""
        # Base queryset
        queryset = ExtractionRequest.objects.filter(deleted_at__isnull=True)
        
        # Apply filters using service function
        queryset = apply_filters_to_queryset(queryset, filters)
        
        # Handle ordering
        ordering = self.request.GET.get('ordering', '-requested_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-requested_at')
        
        return queryset.select_related(
            'requester_agency_unit',
            'requester_agency_unit__agency',
            'requester_authority_position',
            'crime_category',
            'received_by',
            'extraction_unit',
        )
    
    def _get_filter_options(self):
        """Get options for filter dropdowns"""
        current_year = timezone.now().year

        # Load only years that have registered requests
        years_qs = (
            ExtractionRequest.objects
            .filter(deleted_at__isnull=True, requested_at__isnull=False)
            .values_list('requested_at__year', flat=True)
            .distinct()
            .order_by('requested_at__year')
        )
        years = [y for y in years_qs if y]

        return {
            'years': years,
            'extraction_units': list_extraction_units(),
            'agency_units': list_agency_units(),
            'status_choices': [
                ('pending', 'Pendente'),
                ('assigned', 'Aguardando Material'),
                ('received', 'Material Recebido'),
                ('waiting_start', 'Aguardando Início'),
                ('in_progress', 'Em Andamento'),
                ('waiting_collection', 'Aguardando Coleta')
            ]
        }

    def _empty_report(self, filters):
        """Return an empty report structure used when no filters are applied or on error"""
        return {
            'filters_applied': filters,
            'total_requests': 0,
            'summary_by_unit': [],
            'summary_by_status': [],
            'summary_by_month': [],
            'top_requesting_units': [],
            'distribution_efficiency': {
                'completion_rate': 0,
                'avg_processing_time_days': 0,
                'efficiency_score': 0
            },
            'requests_list': [],
            'chart_data': {
                'unit_distribution': [],
                'unit_devices_distribution': [],
                'status_distribution': [],
                'monthly_trend': [],
                'top_requesting_units': []
            },
            'statistics': {
                'total_requests': 0,
                'total_devices': 0,
                'avg_devices_per_request': 0,
                'date_range': {},
                'unique_units': 0,
                'unique_requesters': 0
            }
        }


class DistributionReportPrintView(LoginRequiredMixin, TemplateView):
    """View for printable version of distribution analysis report"""
    
    template_name = 'requisitions/distribution_report_print.html'
    
    def get_context_data(self, **kwargs):
        """Get context data for the print report"""
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters from request
        filters = self._get_filters_from_request()
        
        # Get report data
        try:
            report_data = get_distribution_report(filters)
            
            # Process requests list with same ordering as the regular view
            # (but without pagination since this is for printing)
            requests_queryset = self._get_requests_queryset(filters)
            
            # Update report_data with all requests (no pagination for print)
            requests_data = []
            for request_obj in requests_queryset:
                request_data = {
                    'id': request_obj.id,
                    'status': request_obj.status,
                    'requested_device_amount': request_obj.requested_device_amount,
                    'requested_at': request_obj.requested_at,
                    'request_procedures': request_obj.request_procedures,
                    'requester_agency_unit__name': request_obj.requester_agency_unit.name if request_obj.requester_agency_unit else '',
                    'requester_agency_unit__acronym': request_obj.requester_agency_unit.acronym if request_obj.requester_agency_unit else '',
                    'extraction_unit__name': request_obj.extraction_unit.name if request_obj.extraction_unit else '',
                    'extraction_unit__acronym': request_obj.extraction_unit.acronym if request_obj.extraction_unit else '',
                    'get_status_display': request_obj.get_status_display(),
                    'get_status_color': request_obj.get_status_color()
                }
                requests_data.append(request_data)
            
            report_data['requests_list'] = requests_data
            
        except Exception as e:
            messages.error(self.request, f'Erro ao gerar relatório: {str(e)}')
            report_data = self._empty_report(filters)
        
        # Get central agency and report settings
        try:
            # Get the first ExtractionAgency if exists
            central_agency = ExtractionAgency.objects.filter(deleted_at__isnull=True).first()
        except:
            central_agency = None
            
        try:
            report_settings = ReportsSettings.objects.filter(
                extraction_agency=central_agency,
                deleted_at__isnull=True
            ).first() if central_agency else None
        except:
            report_settings = None
        
        # Prepare chart data JSON (serialize datetimes safely)
        try:
            chart_data_json = json.dumps(report_data.get('chart_data', {}), cls=DjangoJSONEncoder)
        except Exception:
            chart_data_json = json.dumps({'unit_distribution': [], 'status_distribution': [], 'monthly_trend': []})

        context.update({
            'report_data': report_data,
            'filters': filters,
            'central_agency': central_agency,
            'report_settings': report_settings,
            'chart_data_json': chart_data_json
        })
        
        return context
    
    def _get_filters_from_request(self):
        """Extract filters from request parameters"""
        filters = {}
        
        # Year filter
        if self.request.GET.get('year'):
            try:
                filters['year'] = int(self.request.GET.get('year'))
            except ValueError:
                pass
        
        # Date range filters
        if self.request.GET.get('start_date'):
            try:
                filters['start_date'] = datetime.strptime(
                    self.request.GET.get('start_date'), '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        
        if self.request.GET.get('end_date'):
            try:
                filters['end_date'] = datetime.strptime(
                    self.request.GET.get('end_date'), '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        
        # Extraction unit filter
        if self.request.GET.get('extraction_unit'):
            try:
                filters['extraction_unit'] = int(self.request.GET.get('extraction_unit'))
            except ValueError:
                pass
        
        # Status filter
        if self.request.GET.get('status'):
            filters['status'] = self.request.GET.get('status')
        
        # Requester agency unit filter
        if self.request.GET.get('requester_agency_unit'):
            try:
                filters['requester_agency_unit'] = int(self.request.GET.get('requester_agency_unit'))
            except ValueError:
                pass
        
        return filters
    
    def _get_requests_queryset(self, filters):
        """Get queryset for requests list with ordering"""
        # Base queryset
        queryset = ExtractionRequest.objects.filter(deleted_at__isnull=True)
        
        # Apply filters using service function
        queryset = apply_filters_to_queryset(queryset, filters)
        
        # Handle ordering
        ordering = self.request.GET.get('ordering', '-requested_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-requested_at')
        
        return queryset.select_related(
            'requester_agency_unit',
            'requester_agency_unit__agency',
            'requester_authority_position',
            'crime_category',
            'received_by',
            'extraction_unit',
        )
    
    def _empty_report(self, filters):
        """Return an empty report structure used when no filters are applied or on error"""
        return {
            'filters_applied': filters,
            'total_requests': 0,
            'summary_by_unit': [],
            'summary_by_status': [],
            'summary_by_month': [],
            'top_requesting_units': [],
            'distribution_efficiency': {
                'completion_rate': 0,
                'avg_processing_time_days': 0,
                'efficiency_score': 0
            },
            'requests_list': [],
            'chart_data': {
                'unit_distribution': [],
                'unit_devices_distribution': [],
                'status_distribution': [],
                'monthly_trend': [],
                'top_requesting_units': []
            },
            'statistics': {
                'total_requests': 0,
                'total_devices': 0,
                'avg_devices_per_request': 0,
                'date_range': {},
                'unique_units': 0,
                'unique_requesters': 0
            }
        }
    
