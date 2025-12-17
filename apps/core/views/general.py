from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.core.models import (
    ExtractionAgency,
    ExtractionUnit,
    ExtractorUser,
    ExtractionUnitExtractor,
    ExtractionUnitStorageMedia,
    ExtractionUnitEvidenceLocation,
    GeneralSettings,
    EmailSettings,
    ReportsSettings
)
from apps.core.forms import (
    ExtractionAgencyForm,
    ExtractionUnitForm,
    ExtractorUserForm,
    ExtractionUnitExtractorForm,
    ExtractionUnitStorageMediaForm,
    ExtractionUnitEvidenceLocationForm,
    GeneralSettingsForm,
    EmailSettingsForm,
    ReportsSettingsForm
)


def is_staff_user(user):
    """Verifica se o usuário é staff ou superuser"""
    return user.is_staff or user.is_superuser


# ==================== Extraction Agency Views ====================

@login_required
@user_passes_test(is_staff_user)
def extraction_agency_list(request):
    """Lista de agências de extração"""
    agencies = ExtractionAgency.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    return render(request, 'core/extraction_agency_list.html', {'agencies': agencies})


@login_required
@user_passes_test(is_staff_user)
def extraction_agency_create(request):
    """Criar nova agência de extração"""
    if request.method == 'POST':
        form = ExtractionAgencyForm(request.POST, request.FILES)
        if form.is_valid():
            agency = form.save()
            messages.success(request, _('Agência de extração criada com sucesso!'))
            return redirect('core:extraction_agency_detail', pk=agency.pk)
    else:
        form = ExtractionAgencyForm()
    
    return render(request, 'core/extraction_agency_form.html', {'form': form, 'title': _('Nova Agência')})


@login_required
@user_passes_test(is_staff_user)
def extraction_agency_detail(request, pk):
    """Detalhes da agência de extração"""
    agency = get_object_or_404(ExtractionAgency, pk=pk, deleted_at__isnull=True)
    return render(request, 'core/extraction_agency_detail.html', {'agency': agency})


@login_required
@user_passes_test(is_staff_user)
def extraction_agency_edit(request, pk):
    """Editar agência de extração"""
    agency = get_object_or_404(ExtractionAgency, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = ExtractionAgencyForm(request.POST, request.FILES, instance=agency)
        if form.is_valid():
            form.save()
            messages.success(request, _('Agência de extração atualizada com sucesso!'))
            return redirect('core:extraction_agency_detail', pk=agency.pk)
    else:
        form = ExtractionAgencyForm(instance=agency)
    
    return render(request, 'core/extraction_agency_form.html', {
        'form': form, 
        'agency': agency, 
        'title': _('Editar Agência')
    })


@login_required
@user_passes_test(is_staff_user)
def extraction_agency_delete(request, pk):
    """Deletar agência de extração (soft delete)"""
    agency = get_object_or_404(ExtractionAgency, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        from django.utils import timezone
        agency.deleted_at = timezone.now()
        agency.save()
        messages.success(request, _('Agência de extração removida com sucesso!'))
        return redirect('core:extraction_agency_list')
    
    return render(request, 'core/extraction_agency_confirm_delete.html', {'agency': agency})


@login_required
@user_passes_test(is_staff_user)
def extraction_agency_graph(request):
    """
    Exibe a agência central e suas unidades de extração em formato de grafo (Agência -> Unidades).
    Se existir mais de uma agência, permite selecionar via querystring (?agency=<id>).
    """
    agencies = ExtractionAgency.objects.filter(deleted_at__isnull=True).order_by('acronym', 'name')

    agency_id = (request.GET.get('agency') or '').strip()
    if agency_id:
        agency = get_object_or_404(ExtractionAgency, pk=agency_id, deleted_at__isnull=True)
    else:
        agency = agencies.first()

    if not agency:
        messages.warning(request, _('Nenhuma agência cadastrada.'))
        return redirect('core:extraction_agency_list')

    units = ExtractionUnit.objects.filter(
        deleted_at__isnull=True,
        agency=agency
    ).order_by('acronym', 'name')

    context = {
        'agency': agency,
        'agencies': agencies,
        'units': units,
        'page_title': _('Grafo da Agência'),
        'page_icon': 'fa-project-diagram',
        'page_description': _('Visualização hierárquica (Agência → Unidades de Extração)'),
        'selected_agency_id': str(agency.pk),
        'total_units': units.count(),
    }
    return render(request, 'core/extraction_agency_graph.html', context)


# ==================== Extraction Unit Views ====================

@login_required
@user_passes_test(is_staff_user)
def extraction_unit_list(request):
    """Lista de unidades de extração"""
    units = ExtractionUnit.objects.filter(deleted_at__isnull=True).select_related('agency').order_by('-created_at')
    return render(request, 'core/extraction_unit_list.html', {'units': units})


@login_required
@user_passes_test(is_staff_user)
def extraction_unit_create(request):
    """Criar nova unidade de extração"""
    if request.method == 'POST':
        form = ExtractionUnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, _('Unidade de extração criada com sucesso!'))
            return redirect('core:extraction_unit_detail', pk=unit.pk)
    else:
        form = ExtractionUnitForm()
    
    return render(request, 'core/extraction_unit_form.html', {'form': form, 'title': _('Nova Unidade')})


@login_required
@user_passes_test(is_staff_user)
def extraction_unit_detail(request, pk):
    """Detalhes da unidade de extração"""
    unit = get_object_or_404(ExtractionUnit, pk=pk, deleted_at__isnull=True)
    return render(request, 'core/extraction_unit_detail.html', {'unit': unit})


@login_required
@user_passes_test(is_staff_user)
def extraction_unit_edit(request, pk):
    """Editar unidade de extração"""
    unit = get_object_or_404(ExtractionUnit, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = ExtractionUnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, _('Unidade de extração atualizada com sucesso!'))
            return redirect('core:extraction_unit_detail', pk=unit.pk)
    else:
        form = ExtractionUnitForm(instance=unit)
    
    return render(request, 'core/extraction_unit_form.html', {
        'form': form, 
        'unit': unit, 
        'title': _('Editar Unidade')
    })


@login_required
@user_passes_test(is_staff_user)
def extraction_unit_delete(request, pk):
    """Deletar unidade de extração (soft delete)"""
    unit = get_object_or_404(ExtractionUnit, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        from django.utils import timezone
        unit.deleted_at = timezone.now()
        unit.save()
        messages.success(request, _('Unidade de extração removida com sucesso!'))
        return redirect('core:extraction_unit_list')
    
    return render(request, 'core/extraction_unit_confirm_delete.html', {'unit': unit})


# ==================== Extractor User Views ====================

@login_required
@user_passes_test(is_staff_user)
def extractor_user_list(request):
    """Lista de usuários extratores"""
    extractors = ExtractorUser.objects.filter(deleted_at__isnull=True).select_related('user', 'extraction_agency').order_by('-created_at')
    return render(request, 'core/extractor_user_list.html', {'extractors': extractors})


@login_required
@user_passes_test(is_staff_user)
def extractor_user_create(request):
    """Criar novo usuário extrator"""
    if request.method == 'POST':
        form = ExtractorUserForm(request.POST)
        if form.is_valid():
            extractor = form.save()
            messages.success(request, _('Usuário extrator criado com sucesso!'))
            return redirect('core:extractor_user_list')
    else:
        form = ExtractorUserForm()
    
    return render(request, 'core/extractor_user_form.html', {'form': form, 'title': _('Novo Extrator')})


@login_required
@user_passes_test(is_staff_user)
def extractor_user_delete(request, pk):
    """Deletar usuário extrator (soft delete)"""
    extractor = get_object_or_404(ExtractorUser, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        from django.utils import timezone
        extractor.deleted_at = timezone.now()
        extractor.save()
        messages.success(request, _('Usuário extrator removido com sucesso!'))
        return redirect('core:extractor_user_list')
    
    return render(request, 'core/extractor_user_confirm_delete.html', {'extractor': extractor})


# ==================== Extraction Unit Extractor Views ====================

@login_required
@user_passes_test(is_staff_user)
def extraction_unit_extractor_list(request):
    """Lista de associações entre extratores e unidades de extração"""
    associations = ExtractionUnitExtractor.objects.filter(
        deleted_at__isnull=True
    ).select_related(
        'extraction_unit', 'extractor', 'extractor__user', 'extractor__extraction_agency'
    ).order_by('-created_at')
    return render(request, 'core/extraction_unit_extractor_list.html', {'associations': associations})


@login_required
@user_passes_test(is_staff_user)
def extraction_unit_extractor_create(request):
    """Criar nova associação entre extrator e unidade de extração"""
    if request.method == 'POST':
        form = ExtractionUnitExtractorForm(request.POST)
        if form.is_valid():
            association = form.save()
            messages.success(request, _('Associação criada com sucesso!'))
            return redirect('core:extraction_unit_extractor_list')
    else:
        form = ExtractionUnitExtractorForm()
    
    return render(request, 'core/extraction_unit_extractor_form.html', {
        'form': form, 
        'title': _('Nova Associação Extrator-Unidade')
    })


@login_required
@user_passes_test(is_staff_user)
def extraction_unit_extractor_delete(request, pk):
    """Deletar associação entre extrator e unidade de extração (soft delete)"""
    association = get_object_or_404(ExtractionUnitExtractor, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        from django.utils import timezone
        association.deleted_at = timezone.now()
        association.save()
        messages.success(request, _('Associação removida com sucesso!'))
        return redirect('core:extraction_unit_extractor_list')
    
    return render(request, 'core/extraction_unit_extractor_confirm_delete.html', {
        'association': association
    })


# ==================== Storage Media Views ====================

@login_required
@user_passes_test(is_staff_user)
def storage_media_list(request):
    """Lista de meios de armazenamento"""
    media = ExtractionUnitStorageMedia.objects.filter(deleted_at__isnull=True).select_related('extraction_unit').order_by('-created_at')
    return render(request, 'core/storage_media_list.html', {'media_list': media})


@login_required
@user_passes_test(is_staff_user)
def storage_media_create(request):
    """Criar novo meio de armazenamento"""
    if request.method == 'POST':
        form = ExtractionUnitStorageMediaForm(request.POST)
        if form.is_valid():
            media = form.save()
            messages.success(request, _('Meio de armazenamento criado com sucesso!'))
            return redirect('core:storage_media_list')
    else:
        form = ExtractionUnitStorageMediaForm()
    
    return render(request, 'core/storage_media_form.html', {'form': form, 'title': _('Novo Meio de Armazenamento')})


@login_required
@user_passes_test(is_staff_user)
def storage_media_edit(request, pk):
    """Editar meio de armazenamento"""
    media = get_object_or_404(ExtractionUnitStorageMedia, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = ExtractionUnitStorageMediaForm(request.POST, instance=media)
        if form.is_valid():
            form.save()
            messages.success(request, _('Meio de armazenamento atualizado com sucesso!'))
            return redirect('core:storage_media_list')
    else:
        form = ExtractionUnitStorageMediaForm(instance=media)
    
    return render(request, 'core/storage_media_form.html', {
        'form': form, 
        'media': media, 
        'title': _('Editar Meio de Armazenamento')
    })


@login_required
@user_passes_test(is_staff_user)
def storage_media_delete(request, pk):
    """Deletar meio de armazenamento (soft delete)"""
    media = get_object_or_404(ExtractionUnitStorageMedia, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        from django.utils import timezone
        media.deleted_at = timezone.now()
        media.save()
        messages.success(request, _('Meio de armazenamento removido com sucesso!'))
        return redirect('core:storage_media_list')
    
    return render(request, 'core/storage_media_confirm_delete.html', {'media': media})


# ==================== Evidence Location Views ====================

@login_required
@user_passes_test(is_staff_user)
def evidence_location_list(request):
    """Lista de locais de evidências"""
    locations = ExtractionUnitEvidenceLocation.objects.filter(deleted_at__isnull=True).select_related('extraction_unit').order_by('-created_at')
    return render(request, 'core/evidence_location_list.html', {'locations': locations})


@login_required
@user_passes_test(is_staff_user)
def evidence_location_create(request):
    """Criar novo local de evidência"""
    if request.method == 'POST':
        form = ExtractionUnitEvidenceLocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, _('Local de evidência criado com sucesso!'))
            return redirect('core:evidence_location_list')
    else:
        form = ExtractionUnitEvidenceLocationForm()
    
    return render(request, 'core/evidence_location_form.html', {'form': form, 'title': _('Novo Local de Evidência')})


@login_required
@user_passes_test(is_staff_user)
def evidence_location_edit(request, pk):
    """Editar local de evidência"""
    location = get_object_or_404(ExtractionUnitEvidenceLocation, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = ExtractionUnitEvidenceLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, _('Local de evidência atualizado com sucesso!'))
            return redirect('core:evidence_location_list')
    else:
        form = ExtractionUnitEvidenceLocationForm(instance=location)
    
    return render(request, 'core/evidence_location_form.html', {
        'form': form, 
        'location': location, 
        'title': _('Editar Local de Evidência')
    })


@login_required
@user_passes_test(is_staff_user)
def evidence_location_delete(request, pk):
    """Deletar local de evidência (soft delete)"""
    location = get_object_or_404(ExtractionUnitEvidenceLocation, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        from django.utils import timezone
        location.deleted_at = timezone.now()
        location.save()
        messages.success(request, _('Local de evidência removido com sucesso!'))
        return redirect('core:evidence_location_list')
    
    return render(request, 'core/evidence_location_confirm_delete.html', {'location': location})


# ==================== Settings Views ====================

@login_required
@user_passes_test(is_staff_user)
def general_settings(request):
    """Configurações gerais do sistema"""
    try:
        settings = GeneralSettings.objects.first()
    except GeneralSettings.DoesNotExist:
        settings = None
    
    if request.method == 'POST':
        if settings:
            form = GeneralSettingsForm(request.POST, instance=settings)
        else:
            form = GeneralSettingsForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, _('Configurações gerais atualizadas com sucesso!'))
            return redirect('core:general_settings')
    else:
        form = GeneralSettingsForm(instance=settings) if settings else GeneralSettingsForm()
    
    return render(request, 'core/general_settings.html', {'form': form, 'settings': settings})


@login_required
@user_passes_test(is_staff_user)
def email_settings(request):
    """Configurações de e-mail"""
    try:
        settings = EmailSettings.objects.first()
    except EmailSettings.DoesNotExist:
        settings = None
    
    if request.method == 'POST':
        if settings:
            form = EmailSettingsForm(request.POST, instance=settings)
        else:
            form = EmailSettingsForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, _('Configurações de e-mail atualizadas com sucesso!'))
            return redirect('core:email_settings')
    else:
        form = EmailSettingsForm(instance=settings) if settings else EmailSettingsForm()
    
    return render(request, 'core/email_settings.html', {'form': form, 'settings': settings})


@login_required
@user_passes_test(is_staff_user)
def reports_settings(request):
    """Configurações de relatórios"""
    try:
        settings = ReportsSettings.objects.first()
    except ReportsSettings.DoesNotExist:
        settings = None
    
    if request.method == 'POST':
        if settings:
            form = ReportsSettingsForm(request.POST, request.FILES, instance=settings)
        else:
            form = ReportsSettingsForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, _('Configurações de relatórios atualizadas com sucesso!'))
            return redirect('core:reports_settings')
    else:
        form = ReportsSettingsForm(instance=settings) if settings else ReportsSettingsForm()
    
    return render(request, 'core/reports_settings.html', {'form': form, 'settings': settings})


# ==================== User Extractor Management Views ====================

@login_required
@user_passes_test(is_staff_user)
def user_extractor_management(request):
    """
    Página unificada para gerenciar usuários, extratores e associações
    """
    # Busca todos os usuários ativos com seus perfis
    users = User.objects.filter(
        is_active=True
    ).select_related('profile').prefetch_related(
        'extractor_users',
        'extractor_users__extraction_agency',
        'extractor_users__extraction_unit_extractors',
        'extractor_users__extraction_unit_extractors__extraction_unit',
        'extractor_users__extraction_unit_extractors__extraction_unit__agency'
    ).order_by('first_name', 'last_name', 'username')
    
    # Busca todas as agências e unidades para os formulários
    agencies = ExtractionAgency.objects.filter(deleted_at__isnull=True).order_by('acronym')
    units = ExtractionUnit.objects.filter(deleted_at__isnull=True).select_related('agency').order_by('agency__acronym', 'acronym')
    
    context = {
        'users': users,
        'agencies': agencies,
        'units': units,
    }
    
    return render(request, 'core/user_extractor_management.html', context)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def toggle_extractor(request, user_id):
    """
    Adiciona ou remove um usuário como extrator de uma agência
    """
    try:
        user = get_object_or_404(User, pk=user_id, is_active=True)
        agency_id = request.POST.get('agency_id')
        
        if not agency_id:
            return JsonResponse({'success': False, 'message': _('Agência não especificada.')}, status=400)
        
        agency = get_object_or_404(ExtractionAgency, pk=agency_id, deleted_at__isnull=True)
        
        # Verifica se já existe (incluindo deletados)
        try:
            extractor_user = ExtractorUser.objects.get(
                user=user,
                extraction_agency=agency
            )
            
            # Se já existe e está deletado, reativa
            if extractor_user.deleted_at:
                extractor_user.deleted_at = None
                extractor_user.deleted_by = None
                extractor_user.updated_by = request.user
                extractor_user.save()
                return JsonResponse({
                    'success': True,
                    'is_extractor': True,
                    'message': _('Usuário reativado como extrator.')
                })
            else:
                # Se já existe e está ativo, remove (soft delete)
                extractor_user.deleted_at = timezone.now()
                extractor_user.deleted_by = request.user
                extractor_user.save()
                
                # Remove todas as associações com unidades
                ExtractionUnitExtractor.objects.filter(
                    extractor=extractor_user,
                    deleted_at__isnull=True
                ).update(
                    deleted_at=timezone.now(),
                    deleted_by=request.user
                )
                
                return JsonResponse({
                    'success': True,
                    'is_extractor': False,
                    'message': _('Usuário removido como extrator.')
                })
        except ExtractorUser.DoesNotExist:
            # Cria novo
            extractor_user = ExtractorUser.objects.create(
                user=user,
                extraction_agency=agency,
                created_by=request.user
            )
            return JsonResponse({
                'success': True,
                'is_extractor': True,
                'message': _('Usuário adicionado como extrator.')
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def toggle_unit_association(request, extractor_user_id):
    """
    Adiciona ou remove uma associação entre extrator e unidade
    """
    try:
        extractor_user = get_object_or_404(ExtractorUser, pk=extractor_user_id, deleted_at__isnull=True)
        unit_id = request.POST.get('unit_id')
        
        if not unit_id:
            return JsonResponse({'success': False, 'message': _('Unidade não especificada.')}, status=400)
        
        unit = get_object_or_404(ExtractionUnit, pk=unit_id, deleted_at__isnull=True)
        
        # Verifica se a unidade pertence à mesma agência do extrator
        if unit.agency != extractor_user.extraction_agency:
            return JsonResponse({
                'success': False,
                'message': _('A unidade deve pertencer à mesma agência do extrator.')
            }, status=400)
        
        # Verifica se já existe (incluindo deletados)
        try:
            association = ExtractionUnitExtractor.objects.get(
                extraction_unit=unit,
                extractor=extractor_user
            )
            
            # Se já existe e está deletado, reativa
            if association.deleted_at:
                association.deleted_at = None
                association.deleted_by = None
                association.updated_by = request.user
                association.save()
                return JsonResponse({
                    'success': True,
                    'is_associated': True,
                    'message': _('Associação reativada.')
                })
            else:
                # Se já existe e está ativo, remove (soft delete)
                association.deleted_at = timezone.now()
                association.deleted_by = request.user
                association.save()
                
                return JsonResponse({
                    'success': True,
                    'is_associated': False,
                    'message': _('Associação removida.')
                })
        except ExtractionUnitExtractor.DoesNotExist:
            # Cria novo
            association = ExtractionUnitExtractor.objects.create(
                extraction_unit=unit,
                extractor=extractor_user,
                created_by=request.user
            )
            return JsonResponse({
                'success': True,
                'is_associated': True,
                'message': _('Associação criada.')
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["POST"])
def associate_all_units(request, extractor_user_id):
    """
    Associa um extrator a todas as unidades da sua agência
    """
    try:
        extractor_user = get_object_or_404(ExtractorUser, pk=extractor_user_id, deleted_at__isnull=True)
        
        # Busca todas as unidades da agência do extrator
        units = ExtractionUnit.objects.filter(
            agency=extractor_user.extraction_agency,
            deleted_at__isnull=True
        )
        
        created_count = 0
        reactivated_count = 0
        
        for unit in units:
            # Verifica se já existe (incluindo deletados)
            try:
                association = ExtractionUnitExtractor.objects.get(
                    extraction_unit=unit,
                    extractor=extractor_user
                )
                
                # Se está deletado, reativa
                if association.deleted_at:
                    association.deleted_at = None
                    association.deleted_by = None
                    association.updated_by = request.user
                    association.save()
                    reactivated_count += 1
                # Se já está ativo, não faz nada
            except ExtractionUnitExtractor.DoesNotExist:
                # Cria novo
                ExtractionUnitExtractor.objects.create(
                    extraction_unit=unit,
                    extractor=extractor_user,
                    created_by=request.user
                )
                created_count += 1
        
        total = created_count + reactivated_count
        if total > 0:
            message = _('Extrator associado a {total} unidade(s). {created} criada(s), {reactivated} reativada(s).').format(
                total=total,
                created=created_count,
                reactivated=reactivated_count
            )
        else:
            message = _('Extrator já está associado a todas as unidades.')
        
        return JsonResponse({
            'success': True,
            'message': message,
            'created_count': created_count,
            'reactivated_count': reactivated_count,
            'total_count': total
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_http_methods(["GET"])
def get_user_extractor_info(request, user_id):
    """
    Retorna informações sobre o usuário como extrator (JSON)
    """
    try:
        user = get_object_or_404(User, pk=user_id, is_active=True)
        
        extractor_users = ExtractorUser.objects.filter(
            user=user,
            deleted_at__isnull=True
        ).select_related('extraction_agency').prefetch_related(
            'extraction_unit_extractors__extraction_unit',
            'extraction_unit_extractors__extraction_unit__agency'
        )
        
        data = {
            'is_extractor': extractor_users.exists(),
            'extractors': []
        }
        
        for extractor_user in extractor_users:
            units = []
            for association in extractor_user.extraction_unit_extractors.filter(deleted_at__isnull=True):
                units.append({
                    'id': association.extraction_unit.pk,
                    'acronym': association.extraction_unit.acronym,
                    'name': association.extraction_unit.name,
                })
            
            data['extractors'].append({
                'id': extractor_user.pk,
                'agency_id': extractor_user.extraction_agency.pk,
                'agency_acronym': extractor_user.extraction_agency.acronym,
                'agency_name': extractor_user.extraction_agency.name,
                'units': units
            })
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
