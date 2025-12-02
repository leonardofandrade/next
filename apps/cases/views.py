"""
Views para o app cases
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse

from apps.cases.models import Case, CaseDevice, Extraction
from apps.cases.forms import CaseForm, CaseSearchForm, CaseDeviceForm


class CaseListView(LoginRequiredMixin, ListView):
    """
    Lista todos os processos de extração com filtros
    """
    model = Case
    template_name = 'cases/case_list.html'
    context_object_name = 'page_obj'
    paginate_by = 25
    
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
        return context


class CaseDeleteView(LoginRequiredMixin, DeleteView):
    """
    Realiza soft delete de um processo de extração
    """
    model = Case
    template_name = 'cases/case_confirm_delete.html'
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados
        """
        return Case.objects.filter(deleted_at__isnull=True)
    
    def delete(self, request, *args, **kwargs):
        """
        Realiza soft delete ao invés de deletar permanentemente
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
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        context['page_title'] = f'Excluir Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-trash'
        return context


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
        Verifica se o caso existe e não está deletado
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
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
        Verifica se o caso e o dispositivo existem e não estão deletados
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
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
        Verifica se o caso e o dispositivo existem e não estão deletados
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
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
        
        # Verifica se o caso está atribuído ao usuário
        if case.assigned_to != request.user:
            messages.warning(
                request,
                'Este processo não está atribuído a você.'
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
