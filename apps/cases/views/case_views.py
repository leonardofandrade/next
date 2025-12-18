"""
Views relacionadas ao modelo Case
"""
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from typing import Dict, Any
from django.db.models import QuerySet

from apps.core.mixins.views import (
    BaseDetailView, BaseCreateView, BaseUpdateView, 
    BaseDeleteView, ServiceMixin, ExtractionUnitFilterMixin
)
from apps.cases.models import Case, CaseDevice, Extraction, CaseProcedure, CaseDocument
from apps.cases.forms import (
    CaseCreateForm, CaseUpdateForm, CaseSearchForm, 
    CaseDeviceForm, CaseCompleteRegistrationForm, CaseProcedureForm, CaseDocumentForm
)
from apps.core.models import ReportsSettings
from apps.cases.services import CaseService
from apps.core.services.base import ServiceException


class CaseListView(ExtractionUnitFilterMixin, LoginRequiredMixin, ServiceMixin, ListView):
    """
    Lista todos os processos de extração com filtros
    """
    model = Case
    service_class = CaseService
    search_form_class = CaseSearchForm
    template_name = 'cases/case_list.html'
    context_object_name = 'cases'
    paginate_by = settings.PAGINATE_BY
    
    def get_queryset(self) -> QuerySet:
        """Get filtered queryset using service"""
        service = self.get_service()
        filters = self.get_filters()
        
        try:
            return service.list_filtered(filters)
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.model.objects.none()
    
    def get_filters(self) -> Dict[str, Any]:
        """Get filters from request"""
        filters = {}
        
        if self.search_form_class:
            form = self.search_form_class(self.request.GET or None)
            if form.is_valid():
                filters = form.cleaned_data
                
        return {k: v for k, v in filters.items() if v}
    
    def get_context_data(self, **kwargs):
        """Add search form and total count to context"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Processos de Extração'
        context['page_icon'] = 'fa-folder-open'
        context['page_description'] = 'Gerencie todos os processos de extração'
        context['form'] = self.search_form_class(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        context['list_url'] = reverse('cases:list')
        context['clear_url'] = context['list_url']
        return context


class CaseWaitingExtractorListView(CaseListView):
    """
    Lista processos aguardando extrator (status travado em waiting_extractor),
    mantendo os demais filtros disponíveis.
    """

    def get_filters(self) -> Dict[str, Any]:
        filters = super().get_filters()
        filters['status'] = Case.CASE_STATUS_WAITING_EXTRACTOR
        return filters

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Processos - Aguardando Extrator'
        context['page_icon'] = 'fa-user-clock'
        context['page_description'] = 'Processos aguardando atribuição de extrator'
        context['list_url'] = reverse('cases:waiting_extractor_list')
        context['clear_url'] = context['list_url']

        # Exibe o status no filtro, mas trava (o backend força de qualquer forma)
        form = context.get('form')
        if form is not None and hasattr(form, 'fields') and 'status' in form.fields:
            form.fields['status'].initial = Case.CASE_STATUS_WAITING_EXTRACTOR
            form.fields['status'].disabled = True
        context['form'] = form

        return context


class CaseDetailView(ExtractionUnitFilterMixin, BaseDetailView):
    """
    Exibe os detalhes de um processo de extração
    """
    model = Case
    service_class = CaseService
    template_name = 'cases/case_detail.html'
    context_object_name = 'case'
    
    def get_context_data(self, **kwargs):
        """Add page information and counts to context"""
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        case_number = case.number if case.number else f"#{case.pk}"
        acronym = f" - {case.requester_agency_unit.acronym}" if case.requester_agency_unit and case.requester_agency_unit.acronym else ""
        context['page_title'] = f'Processo {case_number}{acronym}'
        context['page_icon'] = 'fa-briefcase'
        
        # Add device, procedure and document counts for complete registration button
        context['devices_count'] = case.case_devices.filter(deleted_at__isnull=True).count()
        context['procedures_count'] = case.procedures.filter(deleted_at__isnull=True).count()
        context['documents_count'] = case.documents.filter(deleted_at__isnull=True).count()
        
        # Add extractions count
        context['extractions_count'] = Extraction.objects.filter(
            case_device__case=case,
            deleted_at__isnull=True
        ).count()
        
        return context


class CaseCreateView(BaseCreateView):
    """
    Cria um novo processo de extração
    """
    model = Case
    form_class = CaseCreateForm
    service_class = CaseService
    template_name = 'cases/case_form_create.html'
    
    def get_form_kwargs(self):
        """Pass current user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        """Set initial data if creating from extraction_request"""
        initial = super().get_initial()
        extraction_request_id = self.request.GET.get('extraction_request')
        
        if extraction_request_id:
            try:
                from apps.requisitions.models import ExtractionRequest
                extraction_request = ExtractionRequest.objects.get(
                    pk=extraction_request_id,
                    deleted_at__isnull=True,
                    case__isnull=True
                )
                initial.update({
                    'requester_agency_unit': extraction_request.requester_agency_unit,
                    'request_procedures': extraction_request.request_procedures,
                    'crime_category': extraction_request.crime_category,
                    'requested_device_amount': extraction_request.requested_device_amount,
                    'requester_reply_email': extraction_request.requester_reply_email,
                    'requester_authority_name': extraction_request.requester_authority_name,
                    'requester_authority_position': extraction_request.requester_authority_position,
                    'extraction_unit': extraction_request.extraction_unit,
                    'additional_info': extraction_request.additional_info,
                })
            except:
                pass
        
        return initial
    
    def form_valid(self, form):
        """Handle form submission with service"""
        service = self.get_service()
        form_data = form.cleaned_data
        
        # A lógica de negócio (status, assigned_at, etc) agora está no service.validate_business_rules()
        try:
            self.object = service.create(form_data)
            messages.success(
                self.request,
                f'Processo criado com sucesso! Aguardando número sequencial.'
            )
            return redirect('cases:detail', pk=self.object.pk)
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Add page information to context"""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Novo Processo'
        context['page_icon'] = 'fa-plus'
        context['action'] = 'create'
        return context


class CaseUpdateView(ExtractionUnitFilterMixin, BaseUpdateView):
    """
    Atualiza um processo de extração existente
    """
    model = Case
    form_class = CaseUpdateForm
    service_class = CaseService
    template_name = 'cases/case_form_update.html'
    
    def get_queryset(self):
        """Filter non-deleted cases and prefetch procedures and devices"""
        queryset = Case.objects.filter(
            deleted_at__isnull=True
        ).prefetch_related(
            'procedures__procedure_category',
            'documents__document_category',
            'case_devices__device_category',
            'case_devices__device_model__brand'
        )
        # Aplica filtro de extraction_unit via mixin
        return super().get_queryset() if hasattr(super(), 'get_queryset') else queryset
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has permission to edit the case"""
        case = self.get_object()
        
        # Allow editing if user is assigned or case has no assignee
        if case.assigned_to and case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para editar este processo. Apenas o responsável pode editá-lo.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Pass current user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle form submission with service"""
        service = self.get_service()
        form_data = form.cleaned_data
        
        # A lógica de negócio (assigned_at, assigned_by) agora está no service.validate_business_rules()
        try:
            self.object = service.update(self.object.pk, form_data)
            messages.success(
                self.request,
                f'Processo atualizado com sucesso!'
            )
            return redirect('cases:detail', pk=self.object.pk)
        except ServiceException as e:
            self.handle_service_exception(e)
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Add page information and counts to context"""
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        context['page_title'] = f'Editar Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-edit'
        context['case'] = case
        context['action'] = 'update'
        
        # Add counts for complete registration button
        context['devices_count'] = case.case_devices.filter(deleted_at__isnull=True).count()
        context['procedures_count'] = case.procedures.filter(deleted_at__isnull=True).count()
        context['documents_count'] = case.documents.filter(deleted_at__isnull=True).count()
        
        # Add procedures to context for the template
        context['procedures'] = case.procedures.filter(deleted_at__isnull=True).select_related('procedure_category')
        
        # Add documents to context for the template
        context['documents'] = case.documents.filter(deleted_at__isnull=True).select_related('document_category')
        
        # Add devices to context for the template
        context['devices'] = case.case_devices.filter(deleted_at__isnull=True).select_related(
            'device_category',
            'device_model__brand'
        )
        
        return context

class CaseUpdateFullView(CaseUpdateView):
    """
    Atualiza um processo de extração existente com todos os campos
    """
    template_name = 'cases/case_form_update_full.html'

    def get_form_kwargs(self):
        """Pass current user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class CaseDeleteView(BaseDeleteView):
    """
    Realiza soft delete de um processo de extração
    """
    model = Case
    service_class = CaseService
    template_name = 'cases/case_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        """Return redirect URL after deletion"""
        return reverse('cases:list')
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has permission to delete the case"""
        case = self.get_object()
        
        # Allow deletion only if user is assigned or case has no assignee
        if case.assigned_to and case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para excluir este processo. Apenas o responsável pode excluí-lo.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add page information to context"""
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        context['page_title'] = f'Excluir Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-trash'
        return context


class CaseCompleteRegistrationView(LoginRequiredMixin, ServiceMixin, View):
    """
    Finaliza o cadastro de um processo e opcionalmente cria extrações
    """
    service_class = CaseService
    template_name = 'cases/case_complete_registration.html'
    
    def get(self, request, pk):
        """
        Exibe o formulário de finalização de cadastro
        """
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o usuário tem permissão
        if case.assigned_to and case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para finalizar o cadastro deste processo. Apenas o responsável pode fazer isso.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        # Verifica se o cadastro já foi finalizado
        if case.registration_completed_at:
            messages.warning(
                request,
                'O cadastro deste processo já foi finalizado.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        # Verifica se há dispositivos cadastrados
        devices_count = case.case_devices.filter(deleted_at__isnull=True).count()
        if devices_count == 0:
            messages.error(
                request,
                'É necessário cadastrar pelo menos um dispositivo antes de finalizar o cadastro do processo.'
            )
            return redirect('cases:update', pk=case.pk)
        
        # Verifica se há procedimentos cadastrados
        procedures_count = case.procedures.filter(deleted_at__isnull=True).count()
        if procedures_count == 0:
            messages.error(
                request,
                'É necessário cadastrar pelo menos um procedimento antes de finalizar o cadastro do processo.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        # Verifica quantos dispositivos não têm extração
        devices_without_extraction = case.case_devices.filter(
            deleted_at__isnull=True,
            device_extraction__isnull=True
        ).count()
        
        form = CaseCompleteRegistrationForm(initial={
            'create_extractions': devices_without_extraction > 0
        })
        
        return render(request, self.template_name, {
            'case': case,
            'form': form,
            'devices_count': devices_count,
            'procedures_count': procedures_count,
            'devices_without_extraction': devices_without_extraction,
            'page_title': f'Finalizar Cadastro - Processo {case.number if case.number else f"#{case.pk}"}',
            'page_icon': 'fa-check-circle',
        })
    
    def post(self, request, pk):
        """
        Processa a finalização do cadastro
        """
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o usuário tem permissão
        if case.assigned_to and case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para finalizar o cadastro deste processo.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        # Verifica se o cadastro já foi finalizado
        if case.registration_completed_at:
            messages.warning(
                request,
                'O cadastro deste processo já foi finalizado.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        # Verifica se há dispositivos cadastrados
        devices_count = case.case_devices.filter(deleted_at__isnull=True).count()
        if devices_count == 0:
            messages.error(
                request,
                'É necessário cadastrar pelo menos um dispositivo antes de finalizar o cadastro do processo.'
            )
            return redirect('cases:update', pk=case.pk)
        
        # Verifica se há procedimentos cadastrados
        procedures_count = case.procedures.filter(deleted_at__isnull=True).count()
        if procedures_count == 0:
            messages.error(
                request,
                'É necessário cadastrar pelo menos um procedimento antes de finalizar o cadastro do processo.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        form = CaseCompleteRegistrationForm(request.POST)
        
        if not form.is_valid():
            devices_without_extraction = case.case_devices.filter(
                deleted_at__isnull=True,
                device_extraction__isnull=True
            ).count()
            
            return render(request, self.template_name, {
                'case': case,
                'form': form,
                'devices_count': devices_count,
                'procedures_count': procedures_count,
                'devices_without_extraction': devices_without_extraction,
                'page_title': f'Finalizar Cadastro - Processo {case.number if case.number else f"#{case.pk}"}',
                'page_icon': 'fa-check-circle',
            })
        
        # Complete registration using service
        service = self.get_service()
        create_extractions = form.cleaned_data.get('create_extractions', False)
        notes = form.cleaned_data.get('notes')
        
        try:
            case = service.complete_registration(case.pk, create_extractions=create_extractions, notes=notes)
            
            # Count created extractions
            created_extractions = 0
            if create_extractions:
                created_extractions = Extraction.objects.filter(
                    case_device__case=case,
                    case_device__deleted_at__isnull=True,
                    deleted_at__isnull=True
                ).count()
            
            # Success message
            if created_extractions > 0:
                messages.success(
                    request,
                    f'Cadastro finalizado com sucesso! {created_extractions} extração(ões) criada(s) automaticamente.'
                )
            else:
                messages.success(
                    request,
                    'Cadastro finalizado com sucesso!'
                )
            
            return redirect('cases:detail', pk=case.pk)
        except ServiceException as e:
            self.handle_service_exception(e)
            return redirect('cases:detail', pk=case.pk)


class CaseDevicesView(LoginRequiredMixin, DetailView):
    """
    Exibe os dispositivos de um processo de extração
    """
    model = Case
    template_name = 'cases/case_devices.html'
    context_object_name = 'case'
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados
        """
        return Case.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona os dispositivos do caso ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        
        # Filtra apenas dispositivos não deletados
        devices = case.case_devices.filter(deleted_at__isnull=True).select_related(
            'device_category',
            'device_model__brand'
        )
        
        # Verifica se está editando um dispositivo
        edit_device_id = self.request.GET.get('edit')
        editing_device = None
        
        if edit_device_id:
            try:
                editing_device = devices.get(pk=edit_device_id)
                # Cria formulário com instância do dispositivo
                form = CaseDeviceForm(instance=editing_device, case=case)
                context['editing_device_id'] = editing_device.pk
            except CaseDevice.DoesNotExist:
                form = CaseDeviceForm(case=case)
                context['editing_device_id'] = None
        else:
            # Cria formulário vazio para criar novo dispositivo
            form = CaseDeviceForm(case=case)
            context['editing_device_id'] = None
        
        context['page_title'] = f'Processo {case.number if case.number else f"#{case.pk}"} - Dispositivos'
        context['page_icon'] = 'fa-mobile-alt'
        context['devices'] = devices
        context['device_form'] = form
        context['action'] = 'create' if not editing_device else 'update'
        
        # Add extractions count
        context['extractions_count'] = Extraction.objects.filter(
            case_device__case=case,
            deleted_at__isnull=True
        ).count()
        
        return context


class CaseProceduresView(LoginRequiredMixin, DetailView):
    """
    Exibe os procedimentos e dispositivos de um processo de extração
    """
    model = Case
    template_name = 'cases/case_procedures.html'
    context_object_name = 'case'
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados
        """
        return Case.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona os procedimentos e dispositivos do caso ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        
        # Filtra apenas procedimentos não deletados
        procedures = case.procedures.filter(deleted_at__isnull=True).select_related('procedure_category')
        
        # Filtra apenas dispositivos não deletados
        devices = case.case_devices.filter(deleted_at__isnull=True).select_related(
            'device_category',
            'device_model__brand'
        )
        
        # Verifica se está editando um procedimento
        edit_procedure_id = self.request.GET.get('edit')
        editing_procedure = None
        
        if edit_procedure_id:
            try:
                editing_procedure = procedures.get(pk=edit_procedure_id)
                # Cria formulário com instância do procedimento
                form = CaseProcedureForm(instance=editing_procedure, case=case)
                context['editing_procedure_id'] = editing_procedure.pk
            except CaseProcedure.DoesNotExist:
                form = CaseProcedureForm(case=case)
                context['editing_procedure_id'] = None
        else:
            # Cria formulário vazio para criar novo procedimento
            form = CaseProcedureForm(case=case)
            context['editing_procedure_id'] = None
        
        context['page_title'] = f'Processo {case.number if case.number else f"#{case.pk}"} - Procedimentos'
        context['page_icon'] = 'fa-gavel'
        context['procedures'] = procedures
        context['procedure_form'] = form
        return context


class CaseDocumentsView(LoginRequiredMixin, DetailView):
    """
    Exibe os documentos de um processo de extração
    """
    model = Case
    template_name = 'cases/case_documents.html'
    context_object_name = 'case'
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados
        """
        return Case.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona os documentos do caso ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        
        # Filtra apenas documentos não deletados
        documents = case.documents.filter(deleted_at__isnull=True).select_related('document_category')
        
        # Verifica se está editando um documento
        edit_document_id = self.request.GET.get('edit')
        editing_document = None
        
        if edit_document_id:
            try:
                editing_document = documents.get(pk=edit_document_id)
                # Cria formulário com instância do documento
                form = CaseDocumentForm(instance=editing_document, case=case)
                context['editing_document_id'] = editing_document.pk
            except CaseDocument.DoesNotExist:
                form = CaseDocumentForm(case=case)
                context['editing_document_id'] = None
        else:
            # Cria formulário vazio para criar novo documento
            form = CaseDocumentForm(case=case)
            context['editing_document_id'] = None
        
        context['page_title'] = f'Processo {case.number if case.number else f"#{case.pk}"} - Documentos'
        context['page_icon'] = 'fa-file-alt'
        context['documents'] = documents
        context['document_form'] = form
        return context
        context['devices'] = devices
        context['procedure_form'] = form
        context['action'] = 'create' if not editing_procedure else 'update'
        
        # Add extractions count
        context['extractions_count'] = Extraction.objects.filter(
            case_device__case=case,
            deleted_at__isnull=True
        ).count()
        
        return context


class CreateExtractionsView(LoginRequiredMixin, ServiceMixin, View):
    """
    Cria extrações para todos os dispositivos do caso que não possuem extração
    """
    service_class = CaseService
    
    def post(self, request, pk):
        """
        Cria extrações com status 'pending' para dispositivos sem extração
        """
        service = self.get_service()
        
        try:
            case = service.get_object(pk)
            
            # Valida se o cadastro do processo foi completado
            if not case.registration_completed_at:
                messages.error(
                    request,
                    'Não é possível criar extrações. Complete o cadastro do processo primeiro.'
                )
                return redirect('cases:detail', pk=case.pk)
            
            extractions = service.create_extractions_for_case(case)
            created_count = len(extractions)
            
            # Coleta informações dos dispositivos para resposta
            devices_info = []
            for extraction in extractions:
                device = extraction.case_device
                device_info = {
                    'id': device.pk,
                    'model': f"{device.device_model.brand.name} - {device.device_model.name}" if device.device_model and device.device_model.brand else 'Sem modelo',
                    'category': device.device_category.name if device.device_category else '-',
                }
                devices_info.append(device_info)
            
            # Adiciona mensagem de sucesso
            if created_count > 0:
                messages.success(
                    request,
                    f'{created_count} extração(ões) criada(s) com sucesso!'
                )
            else:
                messages.info(
                    request,
                    'Nenhuma extração foi criada. Todos os dispositivos já possuem extração.'
                )
            
            # Se a requisição espera JSON, retorna JSON
            if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
                return JsonResponse({
                    'success': True,
                    'created_count': created_count,
                    'devices': devices_info,
                    'message': f'{created_count} extração(ões) criada(s) com sucesso!' if created_count > 0 else 'Nenhuma extração foi criada. Todos os dispositivos já possuem extração.'
                })
            
            # Caso contrário, redireciona para a página de extrações do caso
            return redirect('extractions:case_extractions', pk=case.pk)
            
        except ServiceException as e:
            self.handle_service_exception(e)
            
            # Se a requisição espera JSON, retorna JSON
            if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            # Caso contrário, redireciona de volta
            return redirect('cases:detail', pk=pk)
    
    def get(self, request, pk):
        """
        Retorna informações sobre quantos dispositivos precisam de extração
        """
        try:
            case = get_object_or_404(
                Case.objects.filter(deleted_at__isnull=True),
                pk=pk
            )
            
            # Busca dispositivos do caso que não têm extração associada
            # Para OneToOneField reverso, precisamos usar exclude com valores existentes
            devices_without_extraction = case.case_devices.filter(
                deleted_at__isnull=True
            ).exclude(
                pk__in=Extraction.objects.values_list('case_device_id', flat=True)
            ).select_related(
                'device_category',
                'device_model__brand'
            )
            
            devices_info = []
            for device in devices_without_extraction:
                try:
                    model_str = 'Sem modelo'
                    if device.device_model:
                        if device.device_model.brand:
                            model_str = f"{device.device_model.brand.name} - {device.device_model.name}"
                        else:
                            model_str = device.device_model.name or 'Sem modelo'
                    
                    device_info = {
                        'id': device.pk,
                        'model': model_str,
                        'category': device.device_category.name if device.device_category else '-',
                        'imei': 'Desconhecido' if device.is_imei_unknown else (device.imei_01 or '-'),
                    }
                    devices_info.append(device_info)
                except Exception as e:
                    # Se houver erro ao processar um dispositivo, continua com os outros
                    device_info = {
                        'id': device.pk,
                        'model': 'Erro ao carregar',
                        'category': '-',
                        'imei': '-',
                    }
                    devices_info.append(device_info)
            
            return JsonResponse({
                'devices_count': devices_without_extraction.count(),
                'devices': devices_info,
                'case_number': case.number or 'Rascunho'
            })
        except Exception as e:
            import traceback
            return JsonResponse({
                'error': True,
                'message': str(e),
                'traceback': traceback.format_exc()
            }, status=500)


class CaseAssignToMeView(LoginRequiredMixin, ServiceMixin, View):
    """
    Atribui o processo ao usuário logado
    """
    service_class = CaseService
    
    def post(self, request, pk):
        """
        Atribui o processo ao usuário logado
        """
        service = self.get_service()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            # Verifica se já está atribuído antes de tentar atribuir
            case = service.get_object(pk)
            if case.assigned_to == request.user:
                error_message = 'Este processo já está atribuído a você.'
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    }, status=400)
                messages.warning(request, error_message)
            else:
                case = service.assign_to_user(pk, request.user)
                success_message = 'Processo atribuído a você com sucesso!'
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': success_message
                    })
                messages.success(request, success_message)
        except ServiceException as e:
            error_message = str(e)
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                }, status=400)
            self.handle_service_exception(e)
            # Em caso de erro, também respeita o parâmetro next
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('cases:detail', pk=pk)
        
        # Redireciona priorizando ?next / next (POST), depois referer, senão detalhes
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        referer = request.META.get('HTTP_REFERER')
        if referer and url_has_allowed_host_and_scheme(
            url=referer,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(referer)
        return redirect('cases:detail', pk=pk)


class CaseUnassignFromMeView(LoginRequiredMixin, ServiceMixin, View):
    """
    Remove a atribuição do processo do usuário logado
    """
    service_class = CaseService
    
    def post(self, request, pk):
        """
        Remove a atribuição do processo do usuário logado
        """
        service = self.get_service()
        
        try:
            case = service.unassign_from_user(pk, request.user)
            messages.success(
                request,
                'Atribuição removida com sucesso!'
            )
        except ServiceException as e:
            self.handle_service_exception(e)
            return redirect('cases:detail', pk=pk)
        
        # Redireciona priorizando ?next / next (POST), depois referer, senão detalhes
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        referer = request.META.get('HTTP_REFERER')
        if referer and url_has_allowed_host_and_scheme(
            url=referer,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(referer)
        return redirect('cases:detail', pk=pk)


class CaseCoverPDFView(LoginRequiredMixin, View):
    """
    Gera PDF da capa do processo para impressão
    """
    
    def get(self, request, pk):
        """
        Gera o PDF da capa do processo
        """
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o cadastro foi finalizado
        if not case.registration_completed_at:
            messages.error(
                request,
                'A capa do processo só pode ser gerada após a finalização do cadastro.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        # Busca dispositivos do caso
        devices = case.case_devices.filter(deleted_at__isnull=True).select_related(
            'device_category',
            'device_model__brand'
        )
        
        # Busca procedimentos do caso
        procedures = case.procedures.filter(deleted_at__isnull=True).select_related(
            'procedure_category'
        )
        
        # Prepara dados para tramitações (baseado em eventos do processo)
        tramitacoes = []
        
        # Tramitação inicial: recebimento do processo (da delegacia para NEXT)
        if case.created_at:
            origem_nome = case.requester_agency_unit.name if case.requester_agency_unit else 'DM BARREIRA'
            # Se a unidade solicitante tem sigla, usa ela, senão usa o nome completo
            if case.requester_agency_unit and case.requester_agency_unit.acronym:
                origem_nome = case.requester_agency_unit.acronym
            tramitacoes.append({
                'de': origem_nome,
                'para': case.extraction_unit.acronym if case.extraction_unit else 'NEXT/COIN',
                'data': case.created_at.strftime('%d/%m/%Y'),
                'responsavel': case.created_by.get_full_name() if case.created_by and case.created_by.get_full_name() else (case.created_by.username if case.created_by else 'N/A')
            })
        
        # Tramitação: devolução/finalização (de NEXT para a delegacia)
        if case.finished_at:
            destino_nome = case.requester_agency_unit.name if case.requester_agency_unit else 'BARREIRA'
            # Se a unidade solicitante tem sigla, usa ela, senão usa o nome completo
            if case.requester_agency_unit and case.requester_agency_unit.acronym:
                destino_nome = case.requester_agency_unit.acronym
            elif case.requester_agency_unit:
                # Tenta extrair sigla do nome se possível
                destino_nome = case.requester_agency_unit.name
            tramitacoes.append({
                'de': 'NEXT',
                'para': destino_nome,
                'data': case.finished_at.strftime('%d/%m/%Y'),
                'responsavel': case.finished_by.get_full_name() if case.finished_by and case.finished_by.get_full_name() else (case.finished_by.username if case.finished_by else 'N/A')
            })
        elif case.assigned_at and case.assigned_to:
            # Se não foi finalizado mas foi atribuído, mostra tramitação de atribuição
            destino_nome = case.requester_agency_unit.name if case.requester_agency_unit else 'BARREIRA'
            if case.requester_agency_unit and case.requester_agency_unit.acronym:
                destino_nome = case.requester_agency_unit.acronym
            tramitacoes.append({
                'de': 'NEXT',
                'para': destino_nome,
                'data': case.assigned_at.strftime('%d/%m/%Y'),
                'responsavel': case.assigned_to.get_full_name() if case.assigned_to.get_full_name() else case.assigned_to.username
            })
        
        # Busca documentos do caso
        documents = case.documents.filter(deleted_at__isnull=True).select_related(
            'document_category'
        )
        
        # Busca todos os Ofícios de Solicitação (OFS) nos documentos
        ofs_documents = documents.filter(
            document_category__acronym__iexact='OFS'
        ) if documents else []
        
        # Prepara contexto
        context = {
            'case': case,
            'devices': devices,
            'procedures': procedures,
            'documents': documents,
            'ofs_documents': ofs_documents,
            'tramitacoes': tramitacoes,
            'extraction_unit': case.extraction_unit,
            'requester_agency_unit': case.requester_agency_unit,
        }
        
        # Busca configurações de relatórios
        try:
            reports_settings = ReportsSettings.objects.first()
        except ReportsSettings.DoesNotExist:
            reports_settings = None
        
        # Gera o PDF usando reportlab diretamente
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=1.5*cm, leftMargin=1.5*cm,
                               topMargin=1.5*cm, bottomMargin=1.5*cm)
        
        # Container para os elementos do PDF
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos customizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=5,
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=3,
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=15,
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=8,
        )
        
        bold_style = ParagraphStyle(
            'CustomBold',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=8,
        )
        
        # Cabeçalho - usando configurações de relatórios se disponível
        # Cabeçalho em 3 colunas: logo principal | dados do header | logo secundário
        
        # Primeira coluna: Logo principal
        logo_principal = Spacer(1, 0.1*cm)
        if reports_settings and reports_settings.default_report_header_logo:
            try:
                from reportlab.platypus import Image
                from PIL import Image as PILImage
                # Carrega a imagem para obter dimensões originais
                pil_img = PILImage.open(BytesIO(reports_settings.default_report_header_logo))
                original_width, original_height = pil_img.size
                # Calcula proporção mantendo altura máxima de 2cm
                max_height = 2*cm
                aspect_ratio = original_width / original_height
                calculated_width = max_height * aspect_ratio
                # Limita largura máxima a 2.5cm
                if calculated_width > 2.5*cm:
                    calculated_width = 2.5*cm
                    calculated_height = calculated_width / aspect_ratio
                else:
                    calculated_height = max_height
                # Recria o BytesIO para usar no reportlab
                logo_bytes = BytesIO(reports_settings.default_report_header_logo)
                logo_principal = Image(logo_bytes, width=calculated_width, height=calculated_height)
            except Exception:
                pass
        
        # Segunda coluna: Dados do header (mais larga) - criar uma lista de elementos
        header_elements = []
        if reports_settings:
            if reports_settings.report_cover_header_line_1:
                header_elements.append(Paragraph(reports_settings.report_cover_header_line_1, title_style))
            if reports_settings.report_cover_header_line_2:
                header_elements.append(Paragraph(reports_settings.report_cover_header_line_2, header_style))
            if reports_settings.report_cover_header_line_3:
                header_elements.append(Paragraph(reports_settings.report_cover_header_line_3, subtitle_style))
        else:
            # Cabeçalho padrão se não houver configurações
            header_elements.append(Paragraph("S.S.P.D.S. CEARÁ", title_style))
            header_elements.append(Paragraph("SECRETARIA DA SEGURANÇA PÚBLICA E DEFESA SOCIAL", header_style))
            header_elements.append(Paragraph("COORDENADORIA DE INTELIGÊNCIA", header_style))
            header_elements.append(Paragraph("Célula de Inteligência de Sinais - Núcleo de Extrações", subtitle_style))
        
        # Criar uma tabela interna para a coluna do meio com os textos empilhados
        header_middle_data = [[elem] for elem in header_elements]
        header_middle_table = Table(header_middle_data, colWidths=[10*cm])
        header_middle_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        # Terceira coluna: Logo secundário
        logo_secundario = Spacer(1, 0.1*cm)
        if reports_settings and reports_settings.secondary_report_header_logo:
            try:
                from reportlab.platypus import Image
                from PIL import Image as PILImage
                # Carrega a imagem para obter dimensões originais
                pil_img = PILImage.open(BytesIO(reports_settings.secondary_report_header_logo))
                original_width, original_height = pil_img.size
                # Calcula proporção mantendo altura máxima de 2cm
                max_height = 2*cm
                aspect_ratio = original_width / original_height
                calculated_width = max_height * aspect_ratio
                # Limita largura máxima a 2.5cm
                if calculated_width > 2.5*cm:
                    calculated_width = 2.5*cm
                    calculated_height = calculated_width / aspect_ratio
                else:
                    calculated_height = max_height
                # Recria o BytesIO para usar no reportlab
                logo_bytes = BytesIO(reports_settings.secondary_report_header_logo)
                logo_secundario = Image(logo_bytes, width=calculated_width, height=calculated_height)
            except Exception:
                pass
        
        # Criar tabela de 3 colunas para o cabeçalho
        header_table_data = [[logo_principal, header_middle_table, logo_secundario]]
        header_table = Table(header_table_data, colWidths=[3*cm, 10*cm, 3*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Logo principal à esquerda
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Header centralizado
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),  # Logo secundário à direita
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Número do documento
        extraction_unit_acronym = case.extraction_unit.acronym if case.extraction_unit and case.extraction_unit.acronym else 'NEXT'
        doc_number = f"{case.number or case.pk} - {extraction_unit_acronym}"
        doc_number_style = ParagraphStyle(
            'DocNumber',
            parent=styles['Normal'],
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            alignment=TA_CENTER,
            backColor=colors.lightgrey,
            borderPadding=8,
            spaceAfter=15,
        )
        elements.append(Paragraph(doc_number, doc_number_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Quadro de Assunto
        subject_data = []
        subject_data.append([Paragraph("<b>Assunto</b>", bold_style)])
        subject_data.append([Paragraph("Extração de dados", normal_style)])
        
        subject_table = Table(subject_data, colWidths=[18*cm])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ]))
        elements.append(subject_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Quadro de Procedimentos
        if procedures:
            procedures_data = []
            procedures_data.append([Paragraph("<b>Procedimentos</b>", bold_style)])
            for procedure in procedures:
                if procedure.procedure_category:
                    procedure_text = procedure.procedure_category.name
                    if procedure.number:
                        procedure_text += f" - {procedure.number}"
                    procedures_data.append([Paragraph(procedure_text, normal_style)])
            
            if len(procedures_data) > 1:  # Se há pelo menos um procedimento além do título
                # Largura da página A4 menos margens (21cm - 3cm = 18cm)
                procedures_table = Table(procedures_data, colWidths=[18*cm])
                procedures_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ]))
                elements.append(procedures_table)
                elements.append(Spacer(1, 0.5*cm))
        
        # Quadro de Documentos
        if documents:
            documents_data = []
            documents_data.append([Paragraph("<b>Documentos</b>", bold_style)])
            for document in documents:
                if document.document_category:
                    document_text = document.document_category.name
                    if document.number:
                        document_text += f" - {document.number}"
                    documents_data.append([Paragraph(document_text, normal_style)])
            
            if len(documents_data) > 1:  # Se há pelo menos um documento além do título
                # Largura da página A4 menos margens (21cm - 3cm = 18cm)
                documents_table = Table(documents_data, colWidths=[18*cm])
                documents_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ]))
                elements.append(documents_table)
                elements.append(Spacer(1, 0.5*cm))
        
        # Quadro de Origem
        # Busca todos os Ofícios de Solicitação (OFS) nos documentos
        ofs_documents = documents.filter(
            document_category__acronym__iexact='OFS'
        ) if documents else []
        
        origin_data = []
        origin_data.append([Paragraph("<b>Origem</b>", bold_style)])
        
        # Unidade
        origin_unit = case.requester_agency_unit.name if case.requester_agency_unit else "-"
        origin_data.append([Paragraph(f"<b>Unidade:</b> {origin_unit}", normal_style)])
        
        # E-mail
        if case.requester_reply_email:
            origin_data.append([Paragraph(f"<b>E-mail:</b> {case.requester_reply_email}", normal_style)])
        
        # Autoridade (nome e cargo)
        if case.requester_authority_name:
            autoridade_text = case.requester_authority_name
            if case.requester_authority_position:
                autoridade_text += f" - {case.requester_authority_position.name}"
            origin_data.append([Paragraph(f"<b>Autoridade:</b> {autoridade_text}", normal_style)])
        
        # Ofícios
        if ofs_documents:
            oficio_numbers = []
            for ofs_document in ofs_documents:
                oficio_text = ofs_document.number if ofs_document.number else "-"
                oficio_numbers.append(oficio_text)
            oficio_text = ", ".join(oficio_numbers)
            origin_data.append([Paragraph(f"<b>Ofício:</b> {oficio_text}", normal_style)])
        elif case.extraction_request and case.extraction_request.request_procedures:
            origin_data.append([Paragraph(f"<b>Ofício:</b> {case.extraction_request.request_procedures}", normal_style)])
        
        if len(origin_data) > 1:  # Se há pelo menos um item além do título
            origin_table = Table(origin_data, colWidths=[18*cm])
            origin_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ]))
            elements.append(origin_table)
            elements.append(Spacer(1, 0.5*cm))
        
        # Quadro de Aparelhos
        if devices:
            # Preparar dados dos aparelhos para tabela de 2 colunas
            devices_table_data = []
            # Primeira linha: título que ocupa as 2 colunas
            devices_table_data.append([Paragraph(f"<b>Aparelhos ({len(devices)})</b>", bold_style), ""])
            
            # Dividir dispositivos em pares (2 colunas)
            for i in range(0, len(devices), 2):
                row = []
                # Primeira coluna
                device1 = devices[i]
                device1_text = ""
                if device1.device_model:
                    device1_text = f"{device1.device_model.brand.name} {device1.device_model.name}"
                else:
                    device1_text = "DISPOSITIVO"
                
                if device1.color:
                    device1_text += f" - {device1.color}"
                
                if device1.imei_01:
                    device1_text += f" - IMEI: {device1.imei_01}"
                
                row.append(Paragraph(device1_text, normal_style))
                
                # Segunda coluna (se houver segundo dispositivo)
                if i + 1 < len(devices):
                    device2 = devices[i + 1]
                    device2_text = ""
                    if device2.device_model:
                        device2_text = f"{device2.device_model.brand.name} {device2.device_model.name}"
                    else:
                        device2_text = "DISPOSITIVO"
                    
                    if device2.color:
                        device2_text += f" - {device2.color}"
                    
                    if device2.imei_01:
                        device2_text += f" - IMEI: {device2.imei_01}"
                    
                    row.append(Paragraph(device2_text, normal_style))
                else:
                    # Se não houver segundo dispositivo, deixa vazio
                    row.append(Spacer(1, 0.1*cm))
                
                devices_table_data.append(row)
            
            # Criar tabela do quadro de aparelhos
            devices_table = Table(devices_table_data, colWidths=[9*cm, 9*cm])
            devices_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('SPAN', (0, 0), (-1, 0)),  # Título ocupa as 2 colunas
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ]))
            
            elements.append(devices_table)
            elements.append(Spacer(1, 0.5*cm))
        
        # Quadro de Tramitações
        tramitacoes_box_data = []
        # Título do quadro
        tramitacoes_box_data.append([Paragraph("<b>Tramitações do Processo</b>", bold_style)])
        
        # Tabela de tramitações dentro do quadro
        # Header
        tramitacoes_data = [
            ['DE', 'PARA', 'DATA', 'RESPONSÁVEL']
        ]
        
        # Dados (se houver)
        if tramitacoes:
            for tramitacao in tramitacoes:
                tramitacoes_data.append([
                    tramitacao['de'],
                    tramitacao['para'],
                    tramitacao['data'],
                    tramitacao['responsavel']
                ])
        else:
            # Uma linha vazia se não houver dados
            tramitacoes_data.append(['', '', '', ''])
        
        # Adicionar 5 linhas vazias para preenchimento manual
        for i in range(5):
            tramitacoes_data.append(['', '', '', ''])
        
        tramitacoes_table = Table(tramitacoes_data, colWidths=[4*cm, 4*cm, 3*cm, 5*cm])
        tramitacoes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 0),
        ]))
        
        # Adicionar tabela de tramitações ao quadro
        tramitacoes_box_data.append([tramitacoes_table])
        
        # Criar tabela do quadro de tramitações
        tramitacoes_box_table = Table(tramitacoes_box_data, colWidths=[18*cm])
        tramitacoes_box_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ]))
        
        elements.append(tramitacoes_box_table)
        
        # Rodapé - usando configurações de relatórios se disponível
        if reports_settings:
            elements.append(Spacer(1, 1*cm))
            footer_style = ParagraphStyle(
                'CustomFooter',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=3,
            )
            if reports_settings.report_cover_footer_line_1:
                elements.append(Paragraph(reports_settings.report_cover_footer_line_1, footer_style))
            if reports_settings.report_cover_footer_line_2:
                elements.append(Paragraph(reports_settings.report_cover_footer_line_2, footer_style))
        
        # Gera o PDF
        try:
            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()
            
            # Retorna o PDF como resposta HTTP
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f'capa_processo_{case.number or case.pk}.pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            messages.error(
                request,
                f'Erro ao gerar o PDF da capa: {str(e)}'
            )
            return redirect('cases:detail', pk=case.pk)

