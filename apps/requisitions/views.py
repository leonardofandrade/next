"""
Views para o app requisitions
"""
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.utils import timezone

from apps.requisitions.models import ExtractionRequest
from apps.requisitions.forms import ExtractionRequestForm, ExtractionRequestSearchForm


class ExtractionRequestListView(LoginRequiredMixin, ListView):
    """
    Lista todas as solicitações de extração com filtros
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_list.html'
    context_object_name = 'page_obj'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = ExtractionRequest.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category',
            'created_by',
            'received_by'
        ).order_by('-requested_at', '-created_at')
        
        form = ExtractionRequestSearchForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(request_procedures__icontains=search) |
                    Q(requester_authority_name__icontains=search) |
                    Q(additional_info__icontains=search)
                )
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            requester_agency_unit = form.cleaned_data.get('requester_agency_unit')
            if requester_agency_unit:
                queryset = queryset.filter(requester_agency_unit=requester_agency_unit)
            
            extraction_unit = form.cleaned_data.get('extraction_unit')
            if extraction_unit:
                queryset = queryset.filter(extraction_unit=extraction_unit)
            
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
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Solicitações de Extração'
        context['page_icon'] = 'fa-envelope-open-text'
        context['form'] = ExtractionRequestSearchForm(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context


class ExtractionRequestDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe os detalhes de uma solicitação de extração
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_detail.html'
    context_object_name = 'extraction_request'
    
    def get_queryset(self):
        return ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-file-alt'
        return context


class ExtractionRequestCreateView(LoginRequiredMixin, CreateView):
    """
    Cria uma nova solicitação de extração
    """
    model = ExtractionRequest
    form_class = ExtractionRequestForm
    template_name = 'requisitions/extraction_request_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        extraction_request = form.save(commit=False)
        extraction_request.created_by = self.request.user
        
        # Define requested_at automaticamente
        extraction_request.requested_at = timezone.now()
        
        # Define status baseado na extraction_unit
        if extraction_request.extraction_unit:
            extraction_request.status = ExtractionRequest.REQUEST_STATUS_ASSIGNED
        else:
            extraction_request.status = ExtractionRequest.REQUEST_STATUS_PENDING
        
        extraction_request.save()
        
        messages.success(
            self.request,
            f'Solicitação #{extraction_request.pk} criada com sucesso!'
        )
        
        # Verifica qual ação foi solicitada
        save_and_add_another = self.request.POST.get('save_and_add_another')
        keep_data = self.request.POST.get('keep_data_for_new')
        
        if save_and_add_another or keep_data:
            # Botão "Criar e Adicionar Outra" ou checkbox marcado - mantém dados comuns
            initial_data = {
                'requester_agency_unit': extraction_request.requester_agency_unit.pk if extraction_request.requester_agency_unit else None,
                'requester_reply_email': extraction_request.requester_reply_email,
                'requester_authority_name': extraction_request.requester_authority_name,
                'requester_authority_position': extraction_request.requester_authority_position.pk if extraction_request.requester_authority_position else None,
                'crime_category': extraction_request.crime_category.pk if extraction_request.crime_category else None,
                'extraction_unit': extraction_request.extraction_unit.pk if extraction_request.extraction_unit else None,
            }
            form = ExtractionRequestForm(initial=initial_data, user=self.request.user)
            
            context = self.get_context_data(form=form)
            context['keep_data_checked'] = True
            return self.render_to_response(context)
        
        return redirect('requisitions:detail', pk=extraction_request.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nova Solicitação'
        context['page_icon'] = 'fa-plus'
        context['action'] = 'create'
        return context


class ExtractionRequestUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza uma solicitação de extração existente
    """
    model = ExtractionRequest
    form_class = ExtractionRequestForm
    template_name = 'requisitions/extraction_request_form.html'
    
    def get_queryset(self):
        return ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        extraction_request = form.save(commit=False)
        
        # Armazena o extraction_unit anterior para comparação
        old_extraction_unit = self.object.extraction_unit
        
        extraction_request.updated_by = self.request.user
        extraction_request.version += 1
        
        # Atualiza status se extraction_unit mudou
        new_extraction_unit = extraction_request.extraction_unit
        if old_extraction_unit != new_extraction_unit:
            if new_extraction_unit:
                # Se atribuiu uma unidade, muda para 'assigned'
                if extraction_request.status == ExtractionRequest.REQUEST_STATUS_PENDING:
                    extraction_request.status = ExtractionRequest.REQUEST_STATUS_ASSIGNED
            else:
                # Se removeu a unidade, volta para 'pending'
                if extraction_request.status == ExtractionRequest.REQUEST_STATUS_ASSIGNED:
                    extraction_request.status = ExtractionRequest.REQUEST_STATUS_PENDING
        
        extraction_request.save()
        
        messages.success(
            self.request,
            f'Solicitação #{extraction_request.pk} atualizada com sucesso!'
        )
        return redirect('requisitions:detail', pk=extraction_request.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-edit'
        context['action'] = 'update'
        return context


class ExtractionRequestDeleteView(LoginRequiredMixin, DeleteView):
    """
    Realiza soft delete de uma solicitação de extração
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_confirm_delete.html'
    success_url = None
    
    def get_queryset(self):
        return ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted_at = timezone.now()
        self.object.deleted_by = request.user
        self.object.save()
        
        messages.success(
            request,
            f'Solicitação #{self.object.pk} excluída com sucesso!'
        )
        return redirect('requisitions:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Excluir Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-trash'
        return context


class ExtractionRequestNotReceivedView(LoginRequiredMixin, ListView):
    """
    Lista solicitações não recebidas (pending ou assigned e sem received_at)
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_list.html'
    context_object_name = 'page_obj'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = ExtractionRequest.objects.filter(
            deleted_at__isnull=True,
            received_at__isnull=True,
            status__in=[ExtractionRequest.REQUEST_STATUS_PENDING, ExtractionRequest.REQUEST_STATUS_ASSIGNED]
        ).select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category',
            'created_by'
        ).order_by('-requested_at', '-created_at')
        
        form = ExtractionRequestSearchForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(request_procedures__icontains=search) |
                    Q(requester_authority_name__icontains=search) |
                    Q(additional_info__icontains=search)
                )
            
            status = form.cleaned_data.get('status')
            if status and status in [ExtractionRequest.REQUEST_STATUS_PENDING, ExtractionRequest.REQUEST_STATUS_ASSIGNED]:
                queryset = queryset.filter(status=status)
            
            requester_agency_unit = form.cleaned_data.get('requester_agency_unit')
            if requester_agency_unit:
                queryset = queryset.filter(requester_agency_unit=requester_agency_unit)
            
            extraction_unit = form.cleaned_data.get('extraction_unit')
            if extraction_unit:
                queryset = queryset.filter(extraction_unit=extraction_unit)
            
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
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Solicitações Não Recebidas'
        context['page_icon'] = 'fa-inbox'
        context['form'] = ExtractionRequestSearchForm(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        context['view_type'] = 'not_received'
        return context
