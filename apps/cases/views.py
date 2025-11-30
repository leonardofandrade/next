"""
Views para o app cases
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from apps.cases.models import Case
from apps.cases.forms import CaseForm, CaseSearchForm


@login_required
def case_list(request):
    """
    Lista todos os processos de extração com filtros
    """
    form = CaseSearchForm(request.GET or None)
    
    # Busca todos os processos (exceto deletados)
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
    
    # Aplica filtros
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
    
    # Paginação
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Processos de Extração',
        'page_icon': 'fa-folder-open',
        'form': form,
        'page_obj': page_obj,
        'total_count': queryset.count(),
    }
    
    return render(request, 'cases/case_list.html', context)


@login_required
def case_detail(request, pk):
    """
    Exibe os detalhes de um processo de extração
    """
    case = get_object_or_404(
        Case.objects.filter(deleted_at__isnull=True),
        pk=pk
    )
    
    context = {
        'page_title': f'Processo {case.number if case.number else f"#{case.pk}"}',
        'page_icon': 'fa-file-alt',
        'case': case,
    }
    
    return render(request, 'cases/case_detail.html', context)


@login_required
def case_create(request):
    """
    Cria um novo processo de extração
    """
    if request.method == 'POST':
        form = CaseForm(request.POST, user=request.user)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            
            # Define requested_at automaticamente se não veio de extraction_request
            if not case.requested_at:
                case.requested_at = timezone.now()
            
            # Define status inicial como draft
            case.status = Case.CASE_STATUS_DRAFT
            
            # Se tiver assigned_to, registra assigned_at e assigned_by
            if case.assigned_to:
                case.assigned_at = timezone.now()
                case.assigned_by = request.user
            
            case.save()
            
            messages.success(
                request,
                f'Processo criado com sucesso! Aguardando número sequencial.'
            )
            return redirect('cases:detail', pk=case.pk)
    else:
        # Verifica se está criando a partir de uma extraction_request
        extraction_request_id = request.GET.get('extraction_request')
        initial_data = {}
        
        if extraction_request_id:
            try:
                from apps.requisitions.models import ExtractionRequest
                extraction_request = ExtractionRequest.objects.get(
                    pk=extraction_request_id,
                    deleted_at__isnull=True,
                    case__isnull=True
                )
                initial_data = {
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
                }
            except:
                pass
        
        form = CaseForm(initial=initial_data, user=request.user)
    
    context = {
        'page_title': 'Novo Processo',
        'page_icon': 'fa-plus',
        'form': form,
        'action': 'create',
    }
    
    return render(request, 'cases/case_form.html', context)


@login_required
def case_update(request, pk):
    """
    Atualiza um processo de extração existente
    """
    case = get_object_or_404(
        Case.objects.filter(deleted_at__isnull=True).prefetch_related('procedures__procedure_category'),
        pk=pk
    )
    
    # Armazena o assigned_to anterior para comparação
    old_assigned_to = case.assigned_to
    
    if request.method == 'POST':
        form = CaseForm(
            request.POST,
            instance=case,
            user=request.user
        )
        if form.is_valid():
            case = form.save(commit=False)
            case.updated_by = request.user
            case.version += 1
            
            # Atualiza assigned_at se assigned_to mudou
            new_assigned_to = case.assigned_to
            if old_assigned_to != new_assigned_to and new_assigned_to:
                case.assigned_at = timezone.now()
                case.assigned_by = request.user
            elif not new_assigned_to:
                case.assigned_at = None
                case.assigned_by = None
            
            case.save()
            
            messages.success(
                request,
                f'Processo atualizado com sucesso!'
            )
            return redirect('cases:detail', pk=case.pk)
    else:
        form = CaseForm(instance=case, user=request.user)
    
    context = {
        'page_title': f'Editar Processo {case.number if case.number else f"#{case.pk}"}',
        'page_icon': 'fa-edit',
        'form': form,
        'case': case,
        'action': 'update',
    }
    
    return render(request, 'cases/case_form.html', context)


@login_required
def case_delete(request, pk):
    """
    Realiza soft delete de um processo de extração
    """
    case = get_object_or_404(
        Case.objects.filter(deleted_at__isnull=True),
        pk=pk
    )
    
    if request.method == 'POST':
        case.deleted_at = timezone.now()
        case.deleted_by = request.user
        case.save()
        
        messages.success(
            request,
            f'Processo excluído com sucesso!'
        )
        return redirect('cases:list')
    
    context = {
        'page_title': f'Excluir Processo {case.number if case.number else f"#{case.pk}"}',
        'page_icon': 'fa-trash',
        'case': case,
    }
    
    return render(request, 'cases/case_confirm_delete.html', context)
