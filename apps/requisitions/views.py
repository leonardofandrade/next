"""
Views para o app requisitions
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from apps.requisitions.models import ExtractionRequest
from apps.requisitions.forms import ExtractionRequestForm, ExtractionRequestSearchForm


@login_required
def extraction_request_list(request):
    """
    Lista todas as solicitações de extração com filtros
    """
    form = ExtractionRequestSearchForm(request.GET or None)
    
    # Busca todas as solicitações (exceto deletadas)
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
    
    # Aplica filtros
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
    
    # Paginação
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Solicitações de Extração',
        'page_icon': 'fa-envelope-open-text',
        'form': form,
        'page_obj': page_obj,
        'total_count': queryset.count(),
    }
    
    return render(request, 'requisitions/extraction_request_list.html', context)


@login_required
def extraction_request_detail(request, pk):
    """
    Exibe os detalhes de uma solicitação de extração
    """
    extraction_request = get_object_or_404(
        ExtractionRequest.objects.filter(deleted_at__isnull=True),
        pk=pk
    )
    
    context = {
        'page_title': f'Solicitação #{extraction_request.pk}',
        'page_icon': 'fa-file-alt',
        'extraction_request': extraction_request,
    }
    
    return render(request, 'requisitions/extraction_request_detail.html', context)


@login_required
def extraction_request_create(request):
    """
    Cria uma nova solicitação de extração
    """
    if request.method == 'POST':
        form = ExtractionRequestForm(request.POST, user=request.user)
        if form.is_valid():
            extraction_request = form.save(commit=False)
            extraction_request.created_by = request.user
            
            # Define requested_at automaticamente
            extraction_request.requested_at = timezone.now()
            
            # Define status baseado na extraction_unit
            if extraction_request.extraction_unit:
                extraction_request.status = ExtractionRequest.REQUEST_STATUS_ASSIGNED
            else:
                extraction_request.status = ExtractionRequest.REQUEST_STATUS_PENDING
            
            extraction_request.save()
            
            messages.success(
                request,
                f'Solicitação #{extraction_request.pk} criada com sucesso!'
            )
            
            # Verifica qual ação foi solicitada
            save_and_add_another = request.POST.get('save_and_add_another')
            keep_data = request.POST.get('keep_data_for_new')
            
            if save_and_add_another:
                # Botão "Criar e Adicionar Outra" - mantém dados comuns
                initial_data = {
                    'requester_agency_unit': extraction_request.requester_agency_unit.pk if extraction_request.requester_agency_unit else None,
                    'requester_reply_email': extraction_request.requester_reply_email,
                    'requester_authority_name': extraction_request.requester_authority_name,
                    'requester_authority_position': extraction_request.requester_authority_position.pk if extraction_request.requester_authority_position else None,
                    'crime_category': extraction_request.crime_category.pk if extraction_request.crime_category else None,
                    'extraction_unit': extraction_request.extraction_unit.pk if extraction_request.extraction_unit else None,
                }
                form = ExtractionRequestForm(initial=initial_data, user=request.user)
                
                context = {
                    'page_title': 'Nova Solicitação',
                    'page_icon': 'fa-plus',
                    'form': form,
                    'action': 'create',
                    'keep_data_checked': True,
                }
                return render(request, 'requisitions/extraction_request_form.html', context)
            elif keep_data:
                # Checkbox marcado - mantém dados comuns
                initial_data = {
                    'requester_agency_unit': extraction_request.requester_agency_unit.pk if extraction_request.requester_agency_unit else None,
                    'requester_reply_email': extraction_request.requester_reply_email,
                    'requester_authority_name': extraction_request.requester_authority_name,
                    'requester_authority_position': extraction_request.requester_authority_position.pk if extraction_request.requester_authority_position else None,
                    'crime_category': extraction_request.crime_category.pk if extraction_request.crime_category else None,
                    'extraction_unit': extraction_request.extraction_unit.pk if extraction_request.extraction_unit else None,
                }
                form = ExtractionRequestForm(initial=initial_data, user=request.user)
                
                context = {
                    'page_title': 'Nova Solicitação',
                    'page_icon': 'fa-plus',
                    'form': form,
                    'action': 'create',
                    'keep_data_checked': True,
                }
                return render(request, 'requisitions/extraction_request_form.html', context)
            
            return redirect('requisitions:detail', pk=extraction_request.pk)
    else:
        form = ExtractionRequestForm(user=request.user)
    
    context = {
        'page_title': 'Nova Solicitação',
        'page_icon': 'fa-plus',
        'form': form,
        'action': 'create',
    }
    
    return render(request, 'requisitions/extraction_request_form.html', context)


@login_required
def extraction_request_update(request, pk):
    """
    Atualiza uma solicitação de extração existente
    """
    extraction_request = get_object_or_404(
        ExtractionRequest.objects.filter(deleted_at__isnull=True),
        pk=pk
    )
    
    # Armazena o extraction_unit anterior para comparação
    old_extraction_unit = extraction_request.extraction_unit
    
    if request.method == 'POST':
        form = ExtractionRequestForm(
            request.POST,
            instance=extraction_request,
            user=request.user
        )
        if form.is_valid():
            extraction_request = form.save(commit=False)
            extraction_request.updated_by = request.user
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
                request,
                f'Solicitação #{extraction_request.pk} atualizada com sucesso!'
            )
            return redirect('requisitions:detail', pk=extraction_request.pk)
    else:
        form = ExtractionRequestForm(instance=extraction_request, user=request.user)
    
    context = {
        'page_title': f'Editar Solicitação #{extraction_request.pk}',
        'page_icon': 'fa-edit',
        'form': form,
        'extraction_request': extraction_request,
        'action': 'update',
    }
    
    return render(request, 'requisitions/extraction_request_form.html', context)


@login_required
def extraction_request_delete(request, pk):
    """
    Realiza soft delete de uma solicitação de extração
    """
    extraction_request = get_object_or_404(
        ExtractionRequest.objects.filter(deleted_at__isnull=True),
        pk=pk
    )
    
    if request.method == 'POST':
        extraction_request.deleted_at = timezone.now()
        extraction_request.deleted_by = request.user
        extraction_request.save()
        
        messages.success(
            request,
            f'Solicitação #{extraction_request.pk} excluída com sucesso!'
        )
        return redirect('requisitions:list')
    
    context = {
        'page_title': f'Excluir Solicitação #{extraction_request.pk}',
        'page_icon': 'fa-trash',
        'extraction_request': extraction_request,
    }
    
    return render(request, 'requisitions/extraction_request_confirm_delete.html', context)
