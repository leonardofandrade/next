"""
Views para o app requisitions - Refatoradas usando BaseService e BaseViews
"""
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
from typing import Dict, Any
from django.db.models import QuerySet

from apps.core.mixins.views import (
    BaseListView, BaseDetailView, BaseCreateView, BaseUpdateView, 
    BaseDeleteView, ServiceMixin, ExtractionUnitFilterMixin
)
from apps.requisitions.models import ExtractionRequest
from apps.requisitions.forms import ExtractionRequestForm, ExtractionRequestSearchForm
from apps.requisitions.services import ExtractionRequestService
from apps.cases.models import Case
from apps.core.services.base import ServiceException


class ExtractionRequestListView(ExtractionUnitFilterMixin, BaseListView):
    """
    Lista todas as solicitações de extração com filtros
    """
    model = ExtractionRequest
    service_class = ExtractionRequestService
    search_form_class = ExtractionRequestSearchForm
    template_name = 'requisitions/extraction_request_list.html'
    context_object_name = 'extraction_requests'
    paginate_by = settings.PAGINATE_BY
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Solicitações de Extração'
        context['page_icon'] = 'fa-envelope-open-text'
        context['form'] = context.get('search_form') or self.search_form_class(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context


class ExtractionRequestDetailView(ExtractionUnitFilterMixin, BaseDetailView):
    """
    Exibe os detalhes de uma solicitação de extração
    """
    model = ExtractionRequest
    service_class = ExtractionRequestService
    template_name = 'requisitions/extraction_request_detail.html'
    context_object_name = 'extraction_request'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-file-alt'
        return context


class ExtractionRequestCreateView(BaseCreateView):
    """
    Cria uma nova solicitação de extração
    """
    model = ExtractionRequest
    form_class = ExtractionRequestForm
    service_class = ExtractionRequestService
    template_name = 'requisitions/extraction_request_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        service = self.get_service()
        form_data = form.cleaned_data
        
        # Define requested_at automaticamente se não estiver preenchido
        if not form_data.get('requested_at'):
            form_data['requested_at'] = timezone.now()
        
        # Define status baseado na extraction_unit
        if form_data.get('extraction_unit'):
            form_data['status'] = ExtractionRequest.REQUEST_STATUS_ASSIGNED
        else:
            form_data['status'] = ExtractionRequest.REQUEST_STATUS_PENDING
        
        try:
            self.object = service.create(form_data)
            messages.success(
                self.request,
                f'Solicitação #{self.object.pk} criada com sucesso!'
            )
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.form_invalid(form)
        
        # Verifica qual ação foi solicitada
        save_and_add_another = self.request.POST.get('save_and_add_another')
        keep_data = self.request.POST.get('keep_data_for_new')
        
        if keep_data:
            # Checkbox marcado - mantém dados comuns
            initial_data = {
                'requester_agency_unit': self.object.requester_agency_unit.pk if self.object.requester_agency_unit else None,
                'requester_reply_email': self.object.requester_reply_email,
                'requester_authority_name': self.object.requester_authority_name,
                'requester_authority_position': self.object.requester_authority_position.pk if self.object.requester_authority_position else None,
                'crime_category': self.object.crime_category.pk if self.object.crime_category else None,
                'extraction_unit': self.object.extraction_unit.pk if self.object.extraction_unit else None,
            }
            form = ExtractionRequestForm(initial=initial_data, user=self.request.user)
            
            context = self.get_context_data(form=form)
            context['keep_data_checked'] = True
            return self.render_to_response(context)
        
        if save_and_add_another:
            # Botão "Criar e Adicionar Outra" - redireciona para formulário vazio
            return redirect('requisitions:create')
        
        return redirect('requisitions:update', pk=self.object.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nova Solicitação'
        context['page_icon'] = 'fa-plus'
        context['action'] = 'create'
        
        # Add distribution summary for sidebar
        from apps.requisitions.services import get_distribution_summary
        context['distribution_summary'] = get_distribution_summary()
        
        return context


class ExtractionRequestUpdateView(ExtractionUnitFilterMixin, BaseUpdateView):
    """
    Atualiza uma solicitação de extração existente
    """
    model = ExtractionRequest
    form_class = ExtractionRequestForm
    service_class = ExtractionRequestService
    template_name = 'requisitions/extraction_request_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        service = self.get_service()
        form_data = form.cleaned_data
        
        # Armazena o extraction_unit anterior para comparação
        old_extraction_unit = self.object.extraction_unit
        
        # Define requested_at automaticamente se não estiver preenchido
        if not form_data.get('requested_at'):
            form_data['requested_at'] = timezone.now()
        
        # Atualiza status se extraction_unit mudou
        new_extraction_unit = form_data.get('extraction_unit')
        if old_extraction_unit != new_extraction_unit:
            if new_extraction_unit:
                # Se atribuiu uma unidade, muda para 'assigned'
                if self.object.status == ExtractionRequest.REQUEST_STATUS_PENDING:
                    form_data['status'] = ExtractionRequest.REQUEST_STATUS_ASSIGNED
            else:
                # Se removeu a unidade, volta para 'pending'
                if self.object.status == ExtractionRequest.REQUEST_STATUS_ASSIGNED:
                    form_data['status'] = ExtractionRequest.REQUEST_STATUS_PENDING
        
        try:
            self.object = service.update(self.object.pk, form_data)
            messages.success(
                self.request,
                f'Solicitação #{self.object.pk} atualizada com sucesso!'
            )
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.form_invalid(form)
        
        return redirect('requisitions:detail', pk=self.object.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-edit'
        context['action'] = 'update'
        return context


class ExtractionRequestDeleteView(BaseDeleteView):
    """
    Realiza soft delete de uma solicitação de extração
    """
    model = ExtractionRequest
    service_class = ExtractionRequestService
    template_name = 'requisitions/extraction_request_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('requisitions:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Excluir Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-trash'
        return context


class ExtractionRequestNotReceivedView(ExtractionUnitFilterMixin, LoginRequiredMixin, ServiceMixin, ListView):
    """
    Lista solicitações não recebidas (pending ou assigned e sem received_at)
    """
    model = ExtractionRequest
    service_class = ExtractionRequestService
    search_form_class = ExtractionRequestSearchForm
    template_name = 'requisitions/extraction_request_pending_list.html'
    context_object_name = 'extraction_requests'
    paginate_by = settings.PAGINATE_BY
    
    def get_queryset(self) -> QuerySet:
        """Get not received extraction requests"""
        service = self.get_service()
        queryset = service.get_not_received()
        
        # Aplica filtros do formulário
        filters = self.get_filters()
        if filters:
            # Filtra apenas status permitidos para esta view
            if 'status' in filters and isinstance(filters['status'], list):
                allowed_statuses = [
                    ExtractionRequest.REQUEST_STATUS_PENDING,
                    ExtractionRequest.REQUEST_STATUS_ASSIGNED
                ]
                filters['status'] = [s for s in filters['status'] if s in allowed_statuses]
                if not filters['status']:
                    del filters['status']
            
            queryset = service.apply_filters(queryset, filters)
        
        return queryset
    
    def get_filters(self) -> Dict[str, Any]:
        """Get filters from request"""
        filters = {}
        
        if self.search_form_class:
            form = self.search_form_class(self.request.GET or None)
            if form.is_valid():
                filters = form.cleaned_data
                
        return {k: v for k, v in filters.items() if v}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Solicitações Não Recebidas'
        context['page_icon'] = 'fa-inbox'
        context['form'] = self.search_form_class(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context


class CreateCaseFromRequestView(LoginRequiredMixin, View):
    """
    Cria um Case a partir de um ExtractionRequest
    """
    def post(self, request, pk):
        service = ExtractionRequestService(user=request.user)
        
        # Obtém as observações de recebimento do formulário
        receipt_notes = request.POST.get('receipt_notes', '').strip() or None
        
        try:
            case = service.create_case_from_request(pk, receipt_notes=receipt_notes)
            messages.success(
                request,
                f'Processo criado com sucesso a partir da solicitação #{pk}!'
            )
            return redirect('cases:detail', pk=case.pk)
        except ServiceException as e:
            messages.error(request, str(e))
            return redirect('requisitions:not_received')


class GenerateReplyEmailView(LoginRequiredMixin, View):
    """
    Gera o texto de email de resposta baseado no template da extraction_unit
    """
    def get(self, request, pk):
        extraction_request = get_object_or_404(
            ExtractionRequest.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se há uma extraction_unit associada
        if not extraction_request.extraction_unit:
            # Se for requisição AJAX, retorna JSON de erro
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Esta solicitação não possui uma unidade de extração associada.'
                }, status=400)
            # Caso contrário, redireciona com mensagem
            messages.error(
                request,
                'Esta solicitação não possui uma unidade de extração associada.'
            )
            return redirect('requisitions:detail', pk=pk)
        
        extraction_unit = extraction_request.extraction_unit
        
        # Tenta obter o template das configurações primeiro, depois do modelo direto
        template = None
        subject_template = None
        
        # Tenta obter das configurações (ExtractionUnitSettings) primeiro
        try:
            if hasattr(extraction_unit, 'extraction_unit_settings'):
                settings = extraction_unit.extraction_unit_settings
                if settings and hasattr(settings, 'reply_email_template') and settings.reply_email_template:
                    template = settings.reply_email_template
                if settings and hasattr(settings, 'reply_email_subject') and settings.reply_email_subject:
                    subject_template = settings.reply_email_subject
        except Exception:
            pass
        
        # Se não encontrou nas configurações, tenta no modelo direto
        if not template and extraction_unit.reply_email_template:
            template = extraction_unit.reply_email_template
        
        if not subject_template and extraction_unit.reply_email_subject:
            subject_template = extraction_unit.reply_email_subject
        
        if not template:
            # Se for requisição AJAX, retorna JSON de erro
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'A unidade de extração não possui um template de email de resposta configurado.'
                }, status=400)
            # Caso contrário, redireciona com mensagem
            messages.error(
                request,
                'A unidade de extração não possui um template de email de resposta configurado.'
            )
            return redirect('requisitions:detail', pk=pk)
        
        # Prepara os dados para substituição
        requested_device_amount_str = str(extraction_request.requested_device_amount) if extraction_request.requested_device_amount else 'N/A'
        
        context_data = {
            'procedures': extraction_request.request_procedures or 'N/A',
            'extraction_unit_name': extraction_unit.name or '',
            'extraction_unit_acronym': extraction_unit.acronym or '',
            'extraction_unit_city': extraction_unit.city_name or '',
            'extraction_unit_state': extraction_unit.state_name or '',
            'extraction_unit_postal_code': extraction_unit.postal_code or '',
            'extraction_unit_address': extraction_unit.address_line1 or '',
            'extraction_unit_phone': extraction_unit.primary_phone or '',
            'extraction_unit_secondary_phone': extraction_unit.secondary_phone or '',
            'extraction_unit_email': extraction_unit.primary_email or '',
            'requested_device_amount': requested_device_amount_str,
            'requested_authority_position': requested_device_amount_str,  # Compatibilidade com templates antigos
            'requester_authority_name': extraction_request.requester_authority_name or '',
            'requester_authority_position': extraction_request.requester_authority_position.name if extraction_request.requester_authority_position else '',
            'requester_agency_unit': extraction_request.requester_agency_unit.name if extraction_request.requester_agency_unit else '',
        }
        
        # Substitui os placeholders no template
        email_body = template
        for key, value in context_data.items():
            placeholder = '{' + key + '}'
            email_body = email_body.replace(placeholder, str(value))
        
        # Substitui no assunto também
        email_subject = subject_template or 'Resposta à Solicitação de Extração'
        for key, value in context_data.items():
            placeholder = '{' + key + '}'
            email_subject = email_subject.replace(placeholder, str(value))
        
        # Se for requisição AJAX, retorna JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'subject': email_subject,
                'body': email_body,
                'to': extraction_request.requester_reply_email or '',
            })
        
        # Caso contrário, renderiza uma página com o texto
        return render(request, 'requisitions/generate_reply_email.html', {
            'extraction_request': extraction_request,
            'email_subject': email_subject,
            'email_body': email_body,
            'email_to': extraction_request.requester_reply_email or '',
        })


class ExtractionRequestDistributionListView(ExtractionUnitFilterMixin, LoginRequiredMixin, ServiceMixin, ListView):
    """
    Lista solicitações de extração agrupadas por extraction_unit com resumo (distribuição)
    """
    model = ExtractionRequest
    service_class = ExtractionRequestService
    search_form_class = ExtractionRequestSearchForm
    template_name = 'requisitions/extraction_request_distribution_list.html'
    context_object_name = 'summary_data'
    
    def get_queryset(self):
        """Get queryset with filters applied"""
        service = self.get_service()
        queryset = service.get_queryset()
        
        # Aplica filtros do formulário
        filters = self.get_filters()
        if filters:
            queryset = service.apply_filters(queryset, filters)
        
        return queryset
    
    def get_filters(self) -> Dict[str, Any]:
        """Get filters from request"""
        filters = {}
        
        if self.search_form_class:
            form = self.search_form_class(self.request.GET or None)
            if form.is_valid():
                filters = form.cleaned_data
                
        return {k: v for k, v in filters.items() if v}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = self.get_queryset()
        
        # Agrupa por extraction_unit e calcula estatísticas
        from django.db.models import Count
        
        # Annotate com contagens por status
        summary_data = []
        
        # Busca todas as extraction_units que têm solicitações
        extraction_units = queryset.exclude(
            extraction_unit__isnull=True
        ).values_list('extraction_unit', flat=True).distinct()
        
        from apps.core.models import ExtractionUnit
        
        for unit_id in extraction_units:
            unit_requests = queryset.filter(extraction_unit_id=unit_id)
            unit = unit_requests.first().extraction_unit
            
            # Conta por status
            status_counts = {}
            for status_code, status_label in ExtractionRequest.REQUEST_STATUS_CHOICES:
                status_counts[status_code] = unit_requests.filter(status=status_code).count()
            
            # Total de solicitações
            total = unit_requests.count()
            
            # Solicitações não recebidas
            not_received = unit_requests.filter(
                received_at__isnull=True,
                status__in=[
                    ExtractionRequest.REQUEST_STATUS_PENDING,
                    ExtractionRequest.REQUEST_STATUS_ASSIGNED
                ]
            ).count()
            
            summary_data.append({
                'extraction_unit': unit,
                'total': total,
                'not_received': not_received,
                'status_counts': status_counts,
                'requests': unit_requests.order_by('-requested_at', '-created_at')[:10]  # Últimas 10
            })
        
        # Ordena por total (maior primeiro)
        summary_data.sort(key=lambda x: x['total'], reverse=True)
        
        # Solicitações sem extraction_unit
        requests_without_unit = queryset.filter(extraction_unit__isnull=True)
        if requests_without_unit.exists():
            status_counts_no_unit = {}
            for status_code, status_label in ExtractionRequest.REQUEST_STATUS_CHOICES:
                status_counts_no_unit[status_code] = requests_without_unit.filter(status=status_code).count()
            
            summary_data.append({
                'extraction_unit': None,
                'total': requests_without_unit.count(),
                'not_received': requests_without_unit.filter(
                    received_at__isnull=True,
                    status__in=[
                        ExtractionRequest.REQUEST_STATUS_PENDING,
                        ExtractionRequest.REQUEST_STATUS_ASSIGNED
                    ]
                ).count(),
                'status_counts': status_counts_no_unit,
                'requests': requests_without_unit.order_by('-requested_at', '-created_at')[:10]
            })
        
        context['summary_data'] = summary_data
        context['page_title'] = 'Distribuição por Unidade de Extração'
        context['page_icon'] = 'fa-chart-bar'
        context['form'] = self.search_form_class(self.request.GET or None)
        context['total_count'] = queryset.count()
        
        return context
