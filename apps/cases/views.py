"""
Views para o app cases
"""
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO

from apps.cases.models import Case, CaseDevice, Extraction
from apps.cases.forms import CaseForm, CaseSearchForm, CaseDeviceForm, CaseCompleteRegistrationForm
from apps.core.models import ReportsSettings


class CaseListView(LoginRequiredMixin, ListView):
    """
    Lista todos os processos de extração com filtros
    """
    model = Case
    template_name = 'cases/case_list.html'
    context_object_name = 'page_obj'
    paginate_by = settings.PAGINATE_BY
    
    def get_queryset(self):
        """
        Retorna o queryset filtrado com base nos parâmetros de busca
        """
        queryset = Case.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category',
            'created_by',
            'assigned_to',
            'extraction_request'
        ).annotate(
            devices_count=Count('case_devices', filter=Q(case_devices__deleted_at__isnull=True))
        ).order_by('-priority', '-created_at')
        
        form = CaseSearchForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(number__icontains=search) |
                    Q(request_procedures__icontains=search) |
                    Q(requester_authority_name__icontains=search) |
                    Q(additional_info__icontains=search) |
                    Q(legacy_number__icontains=search)
                )
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            priority = form.cleaned_data.get('priority')
            if priority is not None and priority != '':
                queryset = queryset.filter(priority=int(priority))
            
            requester_agency_unit = form.cleaned_data.get('requester_agency_unit')
            if requester_agency_unit:
                queryset = queryset.filter(requester_agency_unit=requester_agency_unit)
            
            extraction_unit = form.cleaned_data.get('extraction_unit')
            if extraction_unit:
                queryset = queryset.filter(extraction_unit=extraction_unit)
            
            assigned_to = form.cleaned_data.get('assigned_to')
            if assigned_to:
                queryset = queryset.filter(assigned_to=assigned_to)
            
            crime_category = form.cleaned_data.get('crime_category')
            if crime_category:
                queryset = queryset.filter(crime_category=crime_category)
            
            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(requested_at__date__gte=date_from)
            
            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(requested_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Adiciona o formulário de busca e total_count ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Processos de Extração'
        context['page_icon'] = 'fa-folder-open'
        context['form'] = CaseSearchForm(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context


class CaseDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe os detalhes de um processo de extração
    """
    model = Case
    template_name = 'cases/case_detail.html'
    context_object_name = 'case'
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados
        """
        return Case.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        context['page_title'] = f'Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-file-alt'
        
        # Adiciona a contagem de dispositivos e procedimentos para controlar exibição do botão de finalizar cadastro
        context['devices_count'] = case.case_devices.filter(deleted_at__isnull=True).count()
        context['procedures_count'] = case.procedures.filter(deleted_at__isnull=True).count()
        
        return context


class CaseCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um novo processo de extração
    """
    model = Case
    form_class = CaseForm
    template_name = 'cases/case_form.html'
    
    def get_form_kwargs(self):
        """
        Passa o usuário atual para o formulário
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        """
        Define dados iniciais se estiver criando a partir de uma extraction_request
        """
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
                    'extraction_request': extraction_request.pk,
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
        """
        Define campos adicionais antes de salvar
        """
        case = form.save(commit=False)
        case.created_by = self.request.user
        
        # Define requested_at automaticamente se não veio de extraction_request
        if not case.requested_at:
            case.requested_at = timezone.now()
        
        # Define status inicial como draft
        case.status = Case.CASE_STATUS_DRAFT
        
        # Se tiver assigned_to, registra assigned_at e assigned_by
        if case.assigned_to:
            case.assigned_at = timezone.now()
            case.assigned_by = self.request.user
        
        case.save()
        
        messages.success(
            self.request,
            f'Processo criado com sucesso! Aguardando número sequencial.'
        )
        return redirect('cases:detail', pk=case.pk)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Novo Processo'
        context['page_icon'] = 'fa-plus'
        context['action'] = 'create'
        return context


class CaseUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza um processo de extração existente
    """
    model = Case
    form_class = CaseForm
    template_name = 'cases/case_form.html'
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados e faz prefetch de procedures
        """
        return Case.objects.filter(
            deleted_at__isnull=True
        ).prefetch_related('procedures__procedure_category')
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o usuário tem permissão para editar o processo
        """
        case = self.get_object()
        
        # Permite edição se o usuário for o responsável ou se o processo não tiver responsável
        if case.assigned_to and case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para editar este processo. Apenas o responsável pode editá-lo.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """
        Passa o usuário atual para o formulário
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """
        Atualiza campos adicionais antes de salvar
        """
        case = form.save(commit=False)
        old_assigned_to = self.get_object().assigned_to
        
        case.updated_by = self.request.user
        case.version += 1
        
        # Atualiza assigned_at se assigned_to mudou
        new_assigned_to = case.assigned_to
        if old_assigned_to != new_assigned_to and new_assigned_to:
            case.assigned_at = timezone.now()
            case.assigned_by = self.request.user
        elif not new_assigned_to:
            case.assigned_at = None
            case.assigned_by = None
        
        case.save()
        
        messages.success(
            self.request,
            f'Processo atualizado com sucesso!'
        )
        return redirect('cases:detail', pk=case.pk)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        context['page_title'] = f'Editar Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-edit'
        context['case'] = case
        context['action'] = 'update'
        
        # Adiciona contagens para controlar exibição do botão de finalizar cadastro
        context['devices_count'] = case.case_devices.filter(deleted_at__isnull=True).count()
        context['procedures_count'] = case.procedures.filter(deleted_at__isnull=True).count()
        
        return context


class CaseDeleteView(LoginRequiredMixin, DeleteView):
    """
    Realiza soft delete de um processo de extração
    """
    model = Case
    template_name = 'cases/case_confirm_delete.html'
    success_url = None  # Will be set dynamically in get_success_url
    
    def get_success_url(self):
        """
        Retorna a URL de redirecionamento após exclusão
        """
        return reverse('cases:list')
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados
        """
        return Case.objects.filter(deleted_at__isnull=True)
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o usuário tem permissão para excluir o processo
        """
        case = self.get_object()
        
        # Permite exclusão apenas se o usuário for o responsável ou se o processo não tiver responsável
        if case.assigned_to and case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para excluir este processo. Apenas o responsável pode excluí-lo.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """
        Realiza soft delete ao invés de deletar permanentemente
        Override post() para evitar que Django tente fazer hard delete
        """
        case = self.get_object()
        case.deleted_at = timezone.now()
        case.deleted_by = request.user
        case.save()
        
        messages.success(
            request,
            f'Processo excluído com sucesso!'
        )
        return redirect('cases:list')
    
    def delete(self, request, *args, **kwargs):
        """
        Realiza soft delete ao invés de deletar permanentemente
        Mantido para compatibilidade, mas post() é o método principal
        """
        return self.post(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        context['page_title'] = f'Excluir Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-trash'
        return context


class CaseCompleteRegistrationView(LoginRequiredMixin, View):
    """
    Finaliza o cadastro de um processo e opcionalmente cria extrações
    """
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
            return redirect('cases:devices', pk=case.pk)
        
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
            return redirect('cases:devices', pk=case.pk)
        
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
        
        # Finaliza o cadastro
        case.registration_completed_at = timezone.now()
        case.updated_by = request.user
        case.version += 1
        
        # Gera o número do processo se ainda não tiver sido gerado
        if not case.number and case.extraction_unit:
            case_number = case.generate_case_number()
            if case_number:
                case.number = case_number
                case.year = timezone.now().year
        
        # Adiciona observações se fornecidas
        notes = form.cleaned_data.get('notes')
        if notes:
            if case.additional_info:
                case.additional_info += f"\n\n[Finalização de Cadastro - {timezone.now().strftime('%d/%m/%Y %H:%M')}]\n{notes}"
            else:
                case.additional_info = f"[Finalização de Cadastro - {timezone.now().strftime('%d/%m/%Y %H:%M')}]\n{notes}"
        
        case.save()
        
        # Cria extrações se solicitado
        create_extractions = form.cleaned_data.get('create_extractions', False)
        created_extractions = 0
        
        if create_extractions:
            devices_without_extraction = case.case_devices.filter(
                deleted_at__isnull=True,
                device_extraction__isnull=True
            ).select_related('device_category', 'device_model__brand')
            
            for device in devices_without_extraction:
                Extraction.objects.create(
                    case_device=device,
                    status=Extraction.STATUS_PENDING,
                    created_by=request.user
                )
                created_extractions += 1
        
        # Atualiza o status do Case baseado nas extrações
        case.update_status_based_on_extractions()
        
        # Mensagem de sucesso
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
        
        context['page_title'] = f'Dispositivos - Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-mobile-alt'
        context['devices'] = devices
        return context


class CaseDeviceCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um novo dispositivo para um processo
    """
    model = CaseDevice
    form_class = CaseDeviceForm
    template_name = 'cases/case_device_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso existe, não está deletado e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para adicionar dispositivos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para adicionar dispositivos a este processo. Apenas o responsável pode fazer isso.'
            )
            return redirect('cases:devices', pk=self.case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """
        Passa o caso para o formulário
        """
        kwargs = super().get_form_kwargs()
        kwargs['case'] = self.case
        return kwargs
    
    def form_valid(self, form):
        """
        Define campos adicionais antes de salvar
        """
        device = form.save(commit=False)
        device.case = self.case
        device.created_by = self.request.user
        device.save()
        
        # Verifica se deve criar e adicionar outro
        save_and_add_another = self.request.POST.get('save_and_add_another')
        if save_and_add_another == '1':
            messages.success(
                self.request,
                'Dispositivo adicionado com sucesso! Você pode adicionar outro dispositivo abaixo.'
            )
            return redirect('cases:device_create', case_pk=self.case.pk)
        else:
            messages.success(
                self.request,
                'Dispositivo adicionado com sucesso!'
            )
            return redirect('cases:devices', pk=self.case.pk)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Adicionar Dispositivo - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-plus'
        context['case'] = self.case
        context['action'] = 'create'
        return context


class CaseDeviceUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza um dispositivo existente
    """
    model = CaseDevice
    form_class = CaseDeviceForm
    template_name = 'cases/case_device_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso e o dispositivo existem, não estão deletados e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para editar dispositivos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para editar dispositivos deste processo. Apenas o responsável pode fazer isso.'
            )
            return redirect('cases:devices', pk=self.case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtra apenas dispositivos não deletados do caso
        """
        return CaseDevice.objects.filter(
            case=self.case,
            deleted_at__isnull=True
        )
    
    def get_form_kwargs(self):
        """
        Passa o caso para o formulário
        """
        kwargs = super().get_form_kwargs()
        kwargs['case'] = self.case
        return kwargs
    
    def form_valid(self, form):
        """
        Atualiza campos adicionais antes de salvar
        """
        device = form.save(commit=False)
        device.updated_by = self.request.user
        device.version += 1
        device.save()
        
        messages.success(
            self.request,
            'Dispositivo atualizado com sucesso!'
        )
        return redirect('cases:devices', pk=self.case.pk)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar Dispositivo - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-edit'
        context['case'] = self.case
        context['device'] = self.get_object()
        context['action'] = 'update'
        return context


class CaseDeviceDeleteView(LoginRequiredMixin, DeleteView):
    """
    Realiza soft delete de um dispositivo
    """
    model = CaseDevice
    template_name = 'cases/case_device_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso e o dispositivo existem, não estão deletados e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para excluir dispositivos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para excluir dispositivos deste processo. Apenas o responsável pode fazer isso.'
            )
            return redirect('cases:devices', pk=self.case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtra apenas dispositivos não deletados do caso
        """
        return CaseDevice.objects.filter(
            case=self.case,
            deleted_at__isnull=True
        ).select_related(
            'device_category',
            'device_model__brand'
        )
    
    def delete(self, request, *args, **kwargs):
        """
        Realiza soft delete e suporta requisições AJAX
        """
        device = self.get_object()
        device.deleted_at = timezone.now()
        device.deleted_by = request.user
        device.save()
        
        messages.success(
            request,
            'Dispositivo excluído com sucesso!'
        )
        
        # Se for requisição AJAX, retorna JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Dispositivo excluído com sucesso!'
            })
        
        return redirect('cases:devices', pk=self.case.pk)
    
    def get(self, request, *args, **kwargs):
        """
        Suporta requisições AJAX para GET
        """
        device = self.get_object()
        
        # Se for requisição AJAX para GET, retorna dados do dispositivo em JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'device': {
                    'id': device.pk,
                    'category': device.device_category.name if device.device_category else None,
                    'model': f"{device.device_model.brand.name} - {device.device_model.name}" if device.device_model else None,
                    'color': device.color or '-',
                    'imei': 'Desconhecido' if device.is_imei_unknown else (device.imei_01 or '-'),
                    'owner': device.owner_name or '-',
                    'case_number': self.case.number or 'Rascunho',
                    'created_at': device.created_at.strftime('%d/%m/%Y %H:%M') if device.created_at else '-',
                }
            })
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Excluir Dispositivo - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-trash'
        context['case'] = self.case
        return context


class CreateExtractionsView(LoginRequiredMixin, View):
    """
    Cria extrações para todos os dispositivos do caso que não possuem extração
    """
    
    def post(self, request, pk):
        """
        Cria extrações com status 'pending' para dispositivos sem extração
        """
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
        
        created_count = 0
        devices_info = []
        
        for device in devices_without_extraction:
            # Cria extração com status pending
            extraction = Extraction.objects.create(
                case_device=device,
                status=Extraction.STATUS_PENDING,
                created_by=request.user
            )
            created_count += 1
            
            # Coleta informações do dispositivo para resposta
            device_info = {
                'id': device.pk,
                'model': f"{device.device_model.brand.name} - {device.device_model.name}" if device.device_model and device.device_model.brand else 'Sem modelo',
                'category': device.device_category.name if device.device_category else '-',
            }
            devices_info.append(device_info)
        
        # Adiciona mensagem de sucesso
        if created_count > 0:
            # Atualiza o status do Case baseado nas extrações
            case.update_status_based_on_extractions()
            
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


class CaseAssignToMeView(LoginRequiredMixin, View):
    """
    Atribui o processo ao usuário logado
    """
    
    def post(self, request, pk):
        """
        Atribui o processo ao usuário logado
        """
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o caso já está atribuído ao usuário
        if case.assigned_to == request.user:
            messages.warning(
                request,
                'Este processo já está atribuído a você.'
            )
        else:
            # Atribui o caso ao usuário
            case.assigned_to = request.user
            case.assigned_at = timezone.now()
            case.assigned_by = request.user
            case.save()
            
            messages.success(
                request,
                f'Processo atribuído a você com sucesso!'
            )
        
        # Redireciona de acordo com o referer ou para detalhes
        referer = request.META.get('HTTP_REFERER')
        if referer and 'cases/list' in referer:
            return redirect('cases:list')
        return redirect('cases:detail', pk=case.pk)


class CaseUnassignFromMeView(LoginRequiredMixin, View):
    """
    Remove a atribuição do processo do usuário logado
    """
    
    def post(self, request, pk):
        """
        Remove a atribuição do processo do usuário logado
        """
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o caso está atribuído ao usuário (apenas o responsável pode se desatribuir)
        if case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para desatribuir este processo. Apenas o responsável pode se desatribuir.'
            )
        else:
            # Remove a atribuição
            case.assigned_to = None
            case.assigned_at = None
            case.assigned_by = None
            case.save()
            
            messages.success(
                request,
                'Atribuição removida com sucesso!'
            )
        
        # Redireciona de acordo com o referer ou para detalhes
        referer = request.META.get('HTTP_REFERER')
        if referer and 'cases/list' in referer:
            return redirect('cases:list')
        return redirect('cases:detail', pk=case.pk)


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
        
        # Prepara contexto
        context = {
            'case': case,
            'devices': devices,
            'procedures': procedures,
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
        doc_year = case.year if case.year else timezone.now().year
        doc_number = f"{case.number or case.pk}/{doc_year} - NEXT"
        doc_number_style = ParagraphStyle(
            'DocNumber',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_CENTER,
            backColor=colors.lightgrey,
            borderPadding=8,
            spaceAfter=15,
        )
        elements.append(Paragraph(doc_number, doc_number_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Informações do processo
        if case.request_procedures:
            elements.append(Paragraph(f"<b>INQUÉRITO POLICIAL N°:</b> {case.request_procedures}", normal_style))
        
        if case.extraction_request and case.extraction_request.request_procedures:
            elements.append(Paragraph(f"<b>PROCESSO JUDICIAL Nº:</b> {case.extraction_request.request_procedures}", normal_style))
        
        elements.append(Spacer(1, 0.3*cm))
        
        # Duas colunas
        # Coluna esquerda
        left_data = []
        left_data.append([Paragraph("<b>Origem:</b>", bold_style), 
                         Paragraph(case.requester_agency_unit.name if case.requester_agency_unit else "-", normal_style)])
        
        if case.extraction_request and case.extraction_request.request_procedures:
            left_data.append([Paragraph("<b>Ofício nº:</b>", bold_style), 
                             Paragraph(case.extraction_request.request_procedures, normal_style)])
        
        solicitante_text = ""
        if case.requester_authority_name:
            solicitante_text = case.requester_authority_name
            if case.requester_authority_position:
                solicitante_text += f"<br/>{case.requester_authority_position.name}"
        else:
            solicitante_text = "-"
        
        left_data.append([Paragraph("<b>Solicitante:</b>", bold_style), 
                         Paragraph(solicitante_text, normal_style)])
        
        # Coluna direita
        right_data = []
        docs_text = "Ofício;<br/>"
        if procedures:
            for procedure in procedures:
                if procedure.procedure_category:
                    docs_text += f"{procedure.procedure_category.name}"
                    if procedure.number:
                        docs_text += f" - {procedure.number}"
                    docs_text += ";<br/>"
        docs_text += "Termo de Autorização;<br/>Auto de Apresentação e Apreensão;<br/>Formulário de Entrega de Aparelho."
        
        right_data.append([Paragraph("<b>Documentos em anexo:</b>", bold_style), 
                          Paragraph(docs_text, normal_style)])
        
        right_data.append([Spacer(1, 0.2*cm), Spacer(1, 0.2*cm)])
        
        devices_text = "<b>APARELHOS:</b><br/>"
        for idx, device in enumerate(devices, 1):
            device_name = ""
            if device.device_model:
                device_name = f"{device.device_model.brand.name.upper()} {device.device_model.name.upper()}"
            else:
                device_name = "DISPOSITIVO"
            
            devices_text += f"{idx}. {device_name}<br/>"
            
            imeis = []
            if device.imei_01:
                imeis.append(f"({device.imei_01})")
            if device.imei_02:
                imeis.append(f"({device.imei_02})")
            if device.imei_03:
                imeis.append(f"({device.imei_03})")
            if device.imei_04:
                imeis.append(f"({device.imei_04})")
            if device.imei_05:
                imeis.append(f"({device.imei_05})")
            
            if imeis:
                devices_text += "<br/>".join(imeis) + "<br/>"
            devices_text += "<br/>"
        
        if not devices:
            devices_text += "Nenhum dispositivo cadastrado."
        
        right_data.append([Paragraph(devices_text, normal_style)])
        
        # Tabela de duas colunas - usando uma única tabela com 4 colunas
        two_col_data = []
        
        # Linha 1: Origem e Documentos
        two_col_data.append([
            Paragraph("<b>Origem:</b>", bold_style),
            Paragraph(case.requester_agency_unit.name if case.requester_agency_unit else "-", normal_style),
            Paragraph("<b>Documentos em anexo:</b>", bold_style),
            Paragraph("Ofício;", normal_style)
        ])
        
        # Linha 2: Ofício e continuação dos documentos
        oficio_text = "-"
        if case.extraction_request and case.extraction_request.request_procedures:
            oficio_text = case.extraction_request.request_procedures
        
        docs_list = []
        if procedures:
            for procedure in procedures:
                if procedure.procedure_category:
                    proc_text = procedure.procedure_category.name
                    if procedure.number:
                        proc_text += f" - {procedure.number}"
                    docs_list.append(proc_text + ";")
        
        docs_text = "<br/>".join(docs_list) if docs_list else ""
        if docs_text:
            docs_text += "<br/>"
        docs_text += "Termo de Autorização;<br/>Auto de Apresentação e Apreensão;<br/>Formulário de Entrega de Aparelho."
        
        two_col_data.append([
            Paragraph("<b>Ofício nº:</b>", bold_style),
            Paragraph(oficio_text, normal_style),
            Spacer(1, 0.1*cm),
            Paragraph(docs_text, normal_style)
        ])
        
        # Linha 3: Solicitante e cabeçalho dos Aparelhos
        solicitante_text = ""
        if case.requester_authority_name:
            solicitante_text = case.requester_authority_name
            if case.requester_authority_position:
                solicitante_text += f"<br/>{case.requester_authority_position.name}"
        else:
            solicitante_text = "-"
        
        two_col_data.append([
            Paragraph("<b>Solicitante:</b>", bold_style),
            Paragraph(solicitante_text, normal_style),
            Spacer(1, 0.1*cm),
            Spacer(1, 0.1*cm)
        ])
        
        # Tabela de duas colunas com 4 colunas para dados do processo
        two_col_table = Table(two_col_data, colWidths=[2.5*cm, 5.5*cm, 2.5*cm, 5.5*cm])
        two_col_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        elements.append(two_col_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabela de aparelhos em 2 colunas
        elements.append(Paragraph("<b>APARELHOS:</b>", bold_style))
        elements.append(Spacer(1, 0.2*cm))
        
        if devices:
            # Preparar dados dos aparelhos para tabela de 2 colunas
            devices_table_data = []
            # Dividir dispositivos em pares (2 colunas)
            for i in range(0, len(devices), 2):
                row = []
                # Primeira coluna
                device1 = devices[i]
                device1_name = ""
                if device1.device_model:
                    device1_name = f"{device1.device_model.brand.name.upper()} {device1.device_model.name.upper()}"
                else:
                    device1_name = "DISPOSITIVO"
                
                device1_text = f"{i + 1}. {device1_name}"
                imeis1 = []
                if device1.imei_01:
                    imeis1.append(f"({device1.imei_01})")
                if device1.imei_02:
                    imeis1.append(f"({device1.imei_02})")
                if device1.imei_03:
                    imeis1.append(f"({device1.imei_03})")
                if device1.imei_04:
                    imeis1.append(f"({device1.imei_04})")
                if device1.imei_05:
                    imeis1.append(f"({device1.imei_05})")
                
                if imeis1:
                    device1_text += "<br/>" + "<br/>".join(imeis1)
                
                row.append(Paragraph(device1_text, normal_style))
                
                # Segunda coluna (se houver segundo dispositivo)
                if i + 1 < len(devices):
                    device2 = devices[i + 1]
                    device2_name = ""
                    if device2.device_model:
                        device2_name = f"{device2.device_model.brand.name.upper()} {device2.device_model.name.upper()}"
                    else:
                        device2_name = "DISPOSITIVO"
                    
                    device2_text = f"{i + 2}. {device2_name}"
                    imeis2 = []
                    if device2.imei_01:
                        imeis2.append(f"({device2.imei_01})")
                    if device2.imei_02:
                        imeis2.append(f"({device2.imei_02})")
                    if device2.imei_03:
                        imeis2.append(f"({device2.imei_03})")
                    if device2.imei_04:
                        imeis2.append(f"({device2.imei_04})")
                    if device2.imei_05:
                        imeis2.append(f"({device2.imei_05})")
                    
                    if imeis2:
                        device2_text += "<br/>" + "<br/>".join(imeis2)
                    
                    row.append(Paragraph(device2_text, normal_style))
                else:
                    # Se não houver segundo dispositivo, deixa vazio
                    row.append(Spacer(1, 0.1*cm))
                
                devices_table_data.append(row)
            
            # Criar tabela de 2 colunas para aparelhos
            devices_table = Table(devices_table_data, colWidths=[8*cm, 8*cm])
            devices_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            elements.append(devices_table)
        else:
            elements.append(Paragraph("Nenhum dispositivo cadastrado.", normal_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Assunto
        elements.append(Paragraph("<b>Assunto:</b>", bold_style))
        elements.append(Paragraph("Extração de dados", normal_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabela de tramitações
        tramitacoes_data = [
            ['DE', 'PARA', 'DATA', 'RESPONSÁVEL PELO TRAMITE']
        ]
        
        for tramitacao in tramitacoes:
            tramitacoes_data.append([
                tramitacao['de'],
                tramitacao['para'],
                tramitacao['data'],
                tramitacao['responsavel']
            ])
        
        if not tramitacoes:
            tramitacoes_data.append(['', '', '', 'Nenhuma tramitação registrada.'])
        
        tramitacoes_table = Table(tramitacoes_data, colWidths=[4*cm, 4*cm, 3*cm, 5*cm])
        tramitacoes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(Paragraph("<b>TRAMITAÇÕES DO PROCESSO</b>", bold_style))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(tramitacoes_table)
        
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
