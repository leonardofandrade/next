from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

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
