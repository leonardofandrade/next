"""
Views relacionadas ao modelo CaseDocument
"""
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse

from apps.cases.models import Case, CaseDocument
from apps.cases.forms import CaseDocumentForm
from apps.cases.services import CaseDocumentService
from apps.core.services.base import ServiceException
from apps.core.mixins.views import ServiceMixin


class CaseDocumentCreateView(LoginRequiredMixin, ServiceMixin, CreateView):
    """
    Cria um novo documento para um processo
    """
    model = CaseDocument
    form_class = CaseDocumentForm
    service_class = CaseDocumentService
    template_name = 'cases/case_document_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso existe, não está deletado e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para adicionar documentos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para adicionar documentos a este processo. Apenas o responsável pode fazer isso.'
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
        Trata erros de validação - se vier da página de documentos, renderiza lá
        """
        # Se vier da página de documentos, renderiza o template de documents com o formulário
        if self.request.GET.get('from') == 'documents':
            # Recria o contexto da view CaseDocumentsView
            case = self.case
            documents = case.documents.filter(deleted_at__isnull=True).select_related('document_category')
            
            context = {
                'case': case,
                'page_title': f'Processo {case.number if case.number else f"#{case.pk}"} - Documentos',
                'page_icon': 'fa-file-alt',
                'documents': documents,
                'document_form': form,  # Formulário com erros
                'action': 'create',
                'form_errors': form.errors,
                'form_data': form.data,
            }
            
            return render(self.request, 'cases/case_documents.html', context)
        
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """
        Cria documento usando service
        """
        service = self.get_service()
        form_data = form.cleaned_data
        
        # Adiciona o case aos dados
        form_data['case'] = self.case
        
        try:
            document = service.create(form_data)
            
            messages.success(
                self.request,
                'Documento adicionado com sucesso!'
            )
            
            # Se vier da página de documentos, redireciona para lá
            if self.request.GET.get('from') == 'documents':
                return redirect('cases:documents', pk=self.case.pk)
            
            return redirect('cases:update', pk=self.case.pk)
        except ServiceException as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Adicionar Documento - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-plus'
        context['case'] = self.case
        context['action'] = 'create'
        return context


class CaseDocumentDetailView(LoginRequiredMixin, DetailView):
    """
    Retorna dados de um documento em JSON para AJAX
    """
    model = CaseDocument
    
    def get_queryset(self):
        """
        Filtra apenas documentos não deletados
        """
        return CaseDocument.objects.filter(deleted_at__isnull=True)
    
    def get(self, request, *args, **kwargs):
        """
        Retorna dados do documento em JSON
        """
        document = self.get_object()
        
        return JsonResponse({
            'id': document.pk,
            'document_category': document.document_category.pk if document.document_category else None,
            'number': document.number or '',
            'original_filename': document.original_filename or '',
        })


class CaseDocumentUpdateView(LoginRequiredMixin, ServiceMixin, UpdateView):
    """
    Atualiza um documento existente
    """
    model = CaseDocument
    form_class = CaseDocumentForm
    service_class = CaseDocumentService
    template_name = 'cases/case_document_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso e o documento existem, não estão deletados e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para editar documentos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para editar documentos deste processo. Apenas o responsável pode fazer isso.'
            )
            return redirect('cases:update', pk=self.case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtra apenas documentos não deletados do caso
        """
        return CaseDocument.objects.filter(
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
        Trata erros de validação - se vier da página de documentos, renderiza lá
        """
        # Se vier da página de documentos, renderiza o template de documents com o formulário
        if self.request.GET.get('from') == 'documents':
            # Recria o contexto da view CaseDocumentsView
            case = self.case
            documents = case.documents.filter(deleted_at__isnull=True).select_related('document_category')
            
            context = {
                'case': case,
                'page_title': f'Processo {case.number if case.number else f"#{case.pk}"} - Documentos',
                'page_icon': 'fa-file-alt',
                'documents': documents,
                'document_form': form,  # Formulário com erros
                'action': 'update',
                'form_errors': form.errors,
                'form_data': form.data,
                'editing_document_id': self.get_object().pk
            }
            
            return render(self.request, 'cases/case_documents.html', context)
        
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """
        Atualiza documento usando service
        """
        service = self.get_service()
        form_data = form.cleaned_data
        
        # Adiciona o case aos dados (caso não esteja no form_data)
        if 'case' not in form_data:
            form_data['case'] = self.case
        
        try:
            document = service.update(self.get_object().pk, form_data)
            
            messages.success(
                self.request,
                'Documento atualizado com sucesso!'
            )
            
            # Se for requisição AJAX, retorna JSON para recarregar a página
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('cases:documents', kwargs={'pk': self.case.pk})
                })
            
            # Se vier da página de documentos, redireciona para lá (sem o parâmetro edit)
            if self.request.GET.get('from') == 'documents':
                return redirect('cases:documents', pk=self.case.pk)
            
            return redirect('cases:update', pk=self.case.pk)
        except ServiceException as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar Documento - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-edit'
        context['case'] = self.case
        context['document'] = self.get_object()
        context['action'] = 'update'
        return context


class CaseDocumentDeleteView(LoginRequiredMixin, ServiceMixin, DeleteView):
    """
    Realiza soft delete de um documento
    """
    model = CaseDocument
    service_class = CaseDocumentService
    template_name = 'cases/case_document_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        """
        Verifica se o caso e o documento existem, não estão deletados e se o usuário tem permissão
        """
        self.case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=kwargs['case_pk']
        )
        
        # Verifica se o usuário tem permissão para excluir documentos
        if self.case.assigned_to and self.case.assigned_to != request.user:
            messages.error(
                request,
                'Você não tem permissão para excluir documentos deste processo. Apenas o responsável pode fazer isso.'
            )
            # Se for AJAX, retorna JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Você não tem permissão para excluir documentos deste processo.'
                }, status=403)
            return redirect('cases:update', pk=self.case.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtra apenas documentos não deletados do caso
        """
        return CaseDocument.objects.filter(
            case=self.case,
            deleted_at__isnull=True
        ).select_related('document_category')
    
    def get_success_url(self):
        """
        Define a URL de redirecionamento após exclusão
        """
        # Se vier da página de documentos, redireciona para lá
        if self.request.GET.get('from') == 'documents':
            return reverse('cases:documents', kwargs={'pk': self.case.pk})
        
        return reverse('cases:update', kwargs={'pk': self.case.pk})
    
    def delete(self, request, *args, **kwargs):
        """
        Realiza soft delete usando service
        """
        service = self.get_service()
        document_pk = self.get_object().pk
        
        try:
            service.delete(document_pk)
            
            success_message = 'Documento excluído com sucesso!'
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
                    'redirect_url': reverse('cases:documents', kwargs={'pk': self.case.pk})
                })
            
            # Usa get_success_url() para redirecionamento padrão
            return redirect(self.get_success_url())
        except ServiceException as e:
            # Se for AJAX, retorna JSON com erro
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
               request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            self.handle_service_exception(e)
            return redirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações de página ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Excluir Documento - Processo {self.case.number if self.case.number else f"#{self.case.pk}"}'
        context['page_icon'] = 'fa-trash'
        context['case'] = self.case
        return context
