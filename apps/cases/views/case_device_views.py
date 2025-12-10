"""
Views relacionadas ao modelo CaseDevice
"""
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, View
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string

from apps.cases.models import Case, CaseDevice
from apps.cases.forms import CaseDeviceForm
from apps.cases.services import CaseDeviceService
from apps.core.services.base import ServiceException
from apps.core.mixins.views import ServiceMixin


class CaseDeviceCreateView(LoginRequiredMixin, ServiceMixin, CreateView):
    """
    Cria um novo dispositivo para um processo
    """
    model = CaseDevice
    form_class = CaseDeviceForm
    service_class = CaseDeviceService
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
            return redirect('cases:update', pk=self.case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """
        Passa o caso para o formulário
        """
        kwargs = super().get_form_kwargs()
        kwargs['case'] = self.case
        return kwargs
    
    def form_invalid(self, form):
        """
        Trata erros de validação - se vier da página de dispositivos, renderiza lá
        """
        # Se vier da página de dispositivos, renderiza o template de devices com o formulário
        if self.request.GET.get('from') == 'devices':
            # Recria o contexto da view CaseDevicesView
            case = self.case
            devices = case.case_devices.filter(deleted_at__isnull=True).select_related(
                'device_category',
                'device_model__brand'
            )
            
            context = {
                'case': case,
                'page_title': f'Processo {case.number if case.number else f"#{case.pk}"} - Dispositivos',
                'page_icon': 'fa-mobile-alt',
                'devices': devices,
                'device_form': form,  # Formulário com erros
                'action': 'create',
                'editing_device_id': None,  # Importante: define como None para criação
                'form_errors': form.errors,
                'form_data': form.data,
            }
            
            return render(self.request, 'cases/case_devices.html', context)
        
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """
        Cria dispositivo usando service
        """
        service = self.get_service()
        form_data = form.cleaned_data
        
        # Adiciona o case aos dados
        form_data['case'] = self.case
        
        try:
            device = service.create(form_data)
            
            # Verifica se deve criar e adicionar outro
            save_and_add_another = self.request.POST.get('save_and_add_another')
            from_param = self.request.GET.get('from', '')
            
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
                if from_param == 'devices':
                    return redirect('cases:devices', pk=self.case.pk)
                return redirect('cases:update', pk=self.case.pk)
        except ServiceException as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Processo {self.case.number if self.case.number else f"#{self.case.pk}"} - Adicionar Dispositivo'
        context['page_icon'] = 'fa-plus'
        context['case'] = self.case
        context['action'] = 'create'
        return context


class CaseDeviceUpdateView(LoginRequiredMixin, ServiceMixin, UpdateView):
    """
    Atualiza um dispositivo existente
    """
    model = CaseDevice
    form_class = CaseDeviceForm
    service_class = CaseDeviceService
    template_name = 'cases/case_device_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso e o dispositivo existem, não estão deletados e se o usuário tem permissão
        Permite edição por:
        - Responsável pelo caso
        - Extrator responsável pela extração do dispositivo
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica permissão: responsável pelo caso OU extrator responsável pela extração
        has_permission = False
        
        # Verifica se é responsável pelo caso
        if not self.case.assigned_to or self.case.assigned_to == request.user:
            has_permission = True
        
        # Verifica se é extrator responsável pela extração deste dispositivo
        if not has_permission:
            try:
                from apps.core.models import ExtractorUser
                extractor_user = ExtractorUser.objects.get(
                    user=request.user,
                    deleted_at__isnull=True
                )
                # Verifica se há extração atribuída a este extrator para este dispositivo
                device_pk = kwargs.get('pk')
                if device_pk:
                    try:
                        device = CaseDevice.objects.get(
                            pk=device_pk,
                            case=self.case,
                            deleted_at__isnull=True
                        )
                        if hasattr(device, 'device_extraction'):
                            extraction = device.device_extraction
                            if extraction.assigned_to == extractor_user:
                                has_permission = True
                    except CaseDevice.DoesNotExist:
                        pass
            except ExtractorUser.DoesNotExist:
                pass
        
        if not has_permission:
            messages.error(
                request,
                'Você não tem permissão para editar dispositivos deste processo. Apenas o responsável pelo caso ou o extrator responsável pela extração podem fazer isso.'
            )
            return redirect('cases:update', pk=self.case.pk)
        
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
    
    def form_invalid(self, form):
        """
        Trata erros de validação - se vier da página de dispositivos, renderiza lá
        """
        # Se vier da página de dispositivos, renderiza o template de devices com o formulário
        if self.request.GET.get('from') == 'devices':
            # Recria o contexto da view CaseDevicesView
            case = self.case
            devices = case.case_devices.filter(deleted_at__isnull=True).select_related(
                'device_category',
                'device_model__brand'
            )
            
            context = {
                'case': case,
                'page_title': f'Dispositivos - Processo {case.number if case.number else f"#{case.pk}"}',
                'page_icon': 'fa-mobile-alt',
                'devices': devices,
                'device_form': form,  # Formulário com erros
                'action': 'create',
                'form_errors': form.errors,
                'form_data': form.data,
                'editing_device_id': self.get_object().pk
            }
            
            return render(self.request, 'cases/case_devices.html', context)
        
        return super().form_invalid(form)
    
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
    
    def form_valid(self, form):
        """
        Atualiza dispositivo usando service - suporta AJAX
        """
        service = self.get_service()
        form_data = form.cleaned_data
        
        # Adiciona o case aos dados (caso não esteja no form_data)
        if 'case' not in form_data:
            form_data['case'] = self.case
        
        try:
            device = service.update(self.get_object().pk, form_data)
            
            # Se for requisição AJAX, retorna JSON
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Dispositivo atualizado com sucesso!',
                    'redirect_url': self.request.GET.get('next', '')
                })
            
            messages.success(
                self.request,
                'Dispositivo atualizado com sucesso!'
            )
            from_param = self.request.GET.get('from', '')
            if from_param == 'devices':
                return redirect('cases:devices', pk=self.case.pk)
            return redirect('cases:update', pk=self.case.pk)
        except ServiceException as e:
            # Se for AJAX, retorna erro em JSON
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e),
                    'errors': form.errors
                }, status=400)
            form.add_error(None, str(e))
            return self.form_invalid(form)


class CaseDeviceDetailView(LoginRequiredMixin, DetailView):
    """
    Retorna dados de um dispositivo em JSON para AJAX
    """
    model = CaseDevice
    
    def get_queryset(self):
        """
        Filtra apenas dispositivos não deletados
        """
        return CaseDevice.objects.filter(deleted_at__isnull=True).select_related(
            'device_category',
            'device_model__brand'
        )
    
    def get(self, request, *args, **kwargs):
        """
        Retorna dados do dispositivo em JSON
        """
        device = self.get_object()
        
        return JsonResponse({
            'id': device.pk,
            'device_category': device.device_category.pk if device.device_category else None,
            'device_model': device.device_model.pk if device.device_model else None,
            'color': device.color or '',
            'is_imei_unknown': device.is_imei_unknown,
            'imei_01': device.imei_01 or '',
            'imei_02': device.imei_02 or '',
            'imei_03': device.imei_03 or '',
            'imei_04': device.imei_04 or '',
            'imei_05': device.imei_05 or '',
            'owner_name': device.owner_name or '',
            'internal_storage': device.internal_storage or '',
            'is_turned_on': device.is_turned_on,
            'is_locked': device.is_locked,
            'is_password_known': device.is_password_known,
            'password_type': device.password_type or '',
            'password': device.password or '',
            'is_damaged': device.is_damaged,
            'damage_description': device.damage_description or '',
            'has_fluids': device.has_fluids,
            'fluids_description': device.fluids_description or '',
            'has_sim_card': device.has_sim_card,
            'sim_card_info': device.sim_card_info or '',
            'has_memory_card': device.has_memory_card,
            'memory_card_info': device.memory_card_info or '',
            'has_other_accessories': device.has_other_accessories,
            'other_accessories_info': device.other_accessories_info or '',
            'is_sealed': device.is_sealed,
            'security_seal': device.security_seal or '',
            'additional_info': device.additional_info or '',
        })


class CaseDeviceFormModalView(LoginRequiredMixin, View):
    """
    Retorna o formulário de edição de dispositivo para modal AJAX
    Permite edição por:
    - Responsável pelo caso
    - Extrator responsável pela extração do dispositivo
    """
    def get(self, request, case_pk, pk):
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=case_pk
        )
        
        device = get_object_or_404(
            CaseDevice.objects.filter(case=case, deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica permissão: responsável pelo caso OU extrator responsável pela extração
        has_permission = False
        
        # Verifica se é responsável pelo caso
        if not case.assigned_to or case.assigned_to == request.user:
            has_permission = True
        
        # Verifica se é extrator responsável pela extração deste dispositivo
        if not has_permission:
            try:
                from apps.core.models import ExtractorUser
                extractor_user = ExtractorUser.objects.get(
                    user=request.user,
                    deleted_at__isnull=True
                )
                # Verifica se há extração atribuída a este extrator para este dispositivo
                if hasattr(device, 'device_extraction'):
                    extraction = device.device_extraction
                    if extraction.assigned_to == extractor_user:
                        has_permission = True
            except ExtractorUser.DoesNotExist:
                pass
        
        if not has_permission:
            return JsonResponse({
                'success': False,
                'error': 'Você não tem permissão para editar dispositivos deste processo.'
            }, status=403)
        
        form = CaseDeviceForm(instance=device, case=case)
        
        # Verifica se é extrator editando (não responsável pelo caso)
        is_extractor_editing = False
        if case.assigned_to and case.assigned_to != request.user:
            is_extractor_editing = True
        
        # Renderiza apenas o formulário
        form_html = render_to_string('cases/includes/device_form_modal.html', {
            'form': form,
            'device': device,
            'case': case,
            'is_extractor_editing': is_extractor_editing
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'html': form_html
        })


class CaseDeviceDeleteView(LoginRequiredMixin, ServiceMixin, DeleteView):
    """
    Realiza soft delete de um dispositivo
    """
    model = CaseDevice
    service_class = CaseDeviceService
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
            return redirect('cases:update', pk=self.case.pk)
        
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
        Realiza soft delete usando service e suporta requisições AJAX
        """
        service = self.get_service()
        device_pk = self.get_object().pk
        
        try:
            service.delete(device_pk)
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
        except ServiceException as e:
            self.handle_service_exception(e)
            return redirect('cases:devices', pk=self.case.pk)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Excluir Dispositivo - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-trash'
        context['case'] = self.case
        return context

