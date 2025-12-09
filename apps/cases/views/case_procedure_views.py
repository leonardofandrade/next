"""
Views relacionadas ao modelo CaseProcedure
"""
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse

from apps.cases.models import Case, CaseProcedure
from apps.cases.forms import CaseProcedureForm


class CaseProcedureCreateView(LoginRequiredMixin, CreateView):
    """
    Cria um novo procedimento para um processo
    """
    model = CaseProcedure
    form_class = CaseProcedureForm
    template_name = 'cases/case_procedure_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso existe, não está deletado e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para adicionar procedimentos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para adicionar procedimentos a este processo. Apenas o responsável pode fazer isso.'
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
        Trata erros de validação - se vier da página de procedimentos, renderiza lá
        """
        # Se vier da página de procedimentos, renderiza o template de procedures com o formulário
        if self.request.GET.get('from') == 'procedures':
            # Recria o contexto da view CaseProceduresView
            case = self.case
            procedures = case.procedures.filter(deleted_at__isnull=True).select_related('procedure_category')
            devices = case.case_devices.filter(deleted_at__isnull=True).select_related(
                'device_category',
                'device_model__brand'
            )
            
            context = {
                'case': case,
                'page_title': f'Processo {case.number if case.number else f"#{case.pk}"} - Procedimentos',
                'page_icon': 'fa-gavel',
                'procedures': procedures,
                'devices': devices,
                'procedure_form': form,  # Formulário com erros
                'action': 'create',
                'form_errors': form.errors,
                'form_data': form.data,
            }
            
            return render(self.request, 'cases/case_procedures.html', context)
        
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """
        Define campos adicionais antes de salvar
        """
        procedure = form.save(commit=False)
        procedure.case = self.case
        procedure.created_by = self.request.user
        procedure.save()
        
        messages.success(
            self.request,
            'Procedimento adicionado com sucesso!'
        )
        
        # Se vier da página de procedimentos, redireciona para lá
        if self.request.GET.get('from') == 'procedures':
            return redirect('cases:procedures', pk=self.case.pk)
        
        return redirect('cases:update', pk=self.case.pk)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Adicionar Procedimento - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-plus'
        context['case'] = self.case
        context['action'] = 'create'
        return context


class CaseProcedureDetailView(LoginRequiredMixin, DetailView):
    """
    Retorna dados de um procedimento em JSON para AJAX
    """
    model = CaseProcedure
    
    def get_queryset(self):
        """
        Filtra apenas procedimentos não deletados
        """
        return CaseProcedure.objects.filter(deleted_at__isnull=True)
    
    def get(self, request, *args, **kwargs):
        """
        Retorna dados do procedimento em JSON
        """
        procedure = self.get_object()
        
        return JsonResponse({
            'id': procedure.pk,
            'procedure_category': procedure.procedure_category.pk if procedure.procedure_category else None,
            'number': procedure.number or '',
            'original_filename': procedure.original_filename or '',
        })


class CaseProcedureUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza um procedimento existente
    """
    model = CaseProcedure
    form_class = CaseProcedureForm
    template_name = 'cases/case_procedure_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso e o procedimento existem, não estão deletados e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para editar procedimentos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para editar procedimentos deste processo. Apenas o responsável pode fazer isso.'
            )
            return redirect('cases:update', pk=self.case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtra apenas procedimentos não deletados do caso
        """
        return CaseProcedure.objects.filter(
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
        Trata erros de validação - se vier da página de procedimentos, renderiza lá
        """
        # Se vier da página de procedimentos, renderiza o template de procedures com o formulário
        if self.request.GET.get('from') == 'procedures':
            # Recria o contexto da view CaseProceduresView
            case = self.case
            procedures = case.procedures.filter(deleted_at__isnull=True).select_related('procedure_category')
            devices = case.case_devices.filter(deleted_at__isnull=True).select_related(
                'device_category',
                'device_model__brand'
            )
            
            context = {
                'case': case,
                'page_title': f'Processo {case.number if case.number else f"#{case.pk}"} - Procedimentos',
                'page_icon': 'fa-gavel',
                'procedures': procedures,
                'devices': devices,
                'procedure_form': form,  # Formulário com erros
                'action': 'update',
                'form_errors': form.errors,
                'form_data': form.data,
                'editing_procedure_id': self.get_object().pk
            }
            
            return render(self.request, 'cases/case_procedures.html', context)
        
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """
        Atualiza campos adicionais antes de salvar
        """
        procedure = form.save(commit=False)
        procedure.updated_by = self.request.user
        procedure.version += 1
        procedure.save()
        
        messages.success(
            self.request,
            'Procedimento atualizado com sucesso!'
        )
        
        # Se for requisição AJAX, retorna JSON para recarregar a página
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('cases:procedures', kwargs={'pk': self.case.pk})
            })
        
        # Se vier da página de procedimentos, redireciona para lá (sem o parâmetro edit)
        if self.request.GET.get('from') == 'procedures':
            return redirect('cases:procedures', pk=self.case.pk)
        
        return redirect('cases:update', pk=self.case.pk)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar Procedimento - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-edit'
        context['case'] = self.case
        context['procedure'] = self.get_object()
        context['action'] = 'update'
        return context


class CaseProcedureDeleteView(LoginRequiredMixin, DeleteView):
    """
    Realiza soft delete de um procedimento
    """
    model = CaseProcedure
    template_name = 'cases/case_procedure_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso e o procedimento existem, não estão deletados e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para excluir procedimentos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para excluir procedimentos deste processo. Apenas o responsável pode fazer isso.'
            )
            # Se for AJAX, retorna JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Você não tem permissão para excluir procedimentos deste processo.'
                }, status=403)
            return redirect('cases:update', pk=self.case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtra apenas procedimentos não deletados do caso
        """
        return CaseProcedure.objects.filter(
            case=self.case,
            deleted_at__isnull=True
        ).select_related('procedure_category')
    
    def get_success_url(self):
        """
        Define a URL de redirecionamento após exclusão
        """
        # Se vier da página de procedimentos, redireciona para lá
        if self.request.GET.get('from') == 'procedures':
            return reverse('cases:procedures', kwargs={'pk': self.case.pk})
        
        return reverse('cases:update', kwargs={'pk': self.case.pk})
    
    def delete(self, request, *args, **kwargs):
        """
        Realiza soft delete
        """
        procedure = self.get_object()
        procedure.deleted_at = timezone.now()
        procedure.deleted_by = request.user
        procedure.save()
        
        success_message = 'Procedimento excluído com sucesso!'
        messages.success(
            request,
            success_message
        )
        
        # Se for requisição AJAX, retorna JSON com a mensagem
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
           request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': success_message,
                'redirect_url': reverse('cases:procedures', kwargs={'pk': self.case.pk})
            })
        
        # Usa get_success_url() para redirecionamento padrão
        return redirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Excluir Procedimento - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-trash'
        context['case'] = self.case
        return context

