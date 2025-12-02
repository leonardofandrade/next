from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.base_tables.models import (
    Organization,
    Agency,
    Department,
    AgencyUnit,
    EmployeePosition,
    ProcedureCategory,
    CrimeCategory,
    DeviceCategory,
    DeviceBrand,
    DeviceModel
)
from apps.base_tables.forms import (
    OrganizationForm,
    AgencyForm,
    DepartmentForm,
    AgencyUnitForm,
    EmployeePositionForm,
    ProcedureCategoryForm,
    CrimeCategoryForm,
    DeviceCategoryForm,
    DeviceBrandForm,
    DeviceModelForm
)


def is_staff_user(user):
    """Verifica se o usuário é staff ou superuser"""
    return user.is_staff or user.is_superuser


# ==================== Organization Views ====================

@login_required
@user_passes_test(is_staff_user)
def organization_list(request):
    """Lista de instituições"""
    organizations = Organization.objects.filter(deleted_at__isnull=True).order_by('name')
    return render(request, 'base_tables/organization_list.html', {'organizations': organizations})


@login_required
@user_passes_test(is_staff_user)
def organization_create(request):
    """Criar nova instituição"""
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            organization = form.save()
            messages.success(request, _('Instituição criada com sucesso!'))
            return redirect('base_tables:organization_list')
    else:
        form = OrganizationForm()
    
    return render(request, 'base_tables/organization_form.html', {'form': form, 'title': _('Nova Instituição')})


@login_required
@user_passes_test(is_staff_user)
def organization_edit(request, pk):
    """Editar instituição"""
    organization = get_object_or_404(Organization, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, _('Instituição atualizada com sucesso!'))
            return redirect('base_tables:organization_list')
    else:
        form = OrganizationForm(instance=organization)
    
    return render(request, 'base_tables/organization_form.html', {
        'form': form, 
        'organization': organization, 
        'title': _('Editar Instituição')
    })


@login_required
@user_passes_test(is_staff_user)
def organization_delete(request, pk):
    """Deletar instituição (soft delete)"""
    organization = get_object_or_404(Organization, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        organization.deleted_at = timezone.now()
        organization.save()
        messages.success(request, _('Instituição removida com sucesso!'))
        return redirect('base_tables:organization_list')
    
    return render(request, 'base_tables/organization_confirm_delete.html', {'organization': organization})


# ==================== Agency Views ====================

@login_required
@user_passes_test(is_staff_user)
def agency_list(request):
    """Lista de agências"""
    agencies = Agency.objects.filter(deleted_at__isnull=True).select_related('organization').order_by('organization__name', 'name')
    return render(request, 'base_tables/agency_list.html', {'agencies': agencies})


@login_required
@user_passes_test(is_staff_user)
def agency_create(request):
    """Criar nova agência"""
    if request.method == 'POST':
        form = AgencyForm(request.POST)
        if form.is_valid():
            agency = form.save()
            messages.success(request, _('Agência criada com sucesso!'))
            return redirect('base_tables:agency_list')
    else:
        form = AgencyForm()
    
    return render(request, 'base_tables/agency_form.html', {'form': form, 'title': _('Nova Agência')})


@login_required
@user_passes_test(is_staff_user)
def agency_edit(request, pk):
    """Editar agência"""
    agency = get_object_or_404(Agency, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = AgencyForm(request.POST, instance=agency)
        if form.is_valid():
            form.save()
            messages.success(request, _('Agência atualizada com sucesso!'))
            return redirect('base_tables:agency_list')
    else:
        form = AgencyForm(instance=agency)
    
    return render(request, 'base_tables/agency_form.html', {
        'form': form, 
        'agency': agency, 
        'title': _('Editar Agência')
    })


@login_required
@user_passes_test(is_staff_user)
def agency_delete(request, pk):
    """Deletar agência (soft delete)"""
    agency = get_object_or_404(Agency, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        agency.deleted_at = timezone.now()
        agency.save()
        messages.success(request, _('Agência removida com sucesso!'))
        return redirect('base_tables:agency_list')
    
    return render(request, 'base_tables/agency_confirm_delete.html', {'agency': agency})


# ==================== Department Views ====================

@login_required
@user_passes_test(is_staff_user)
def department_list(request):
    """Lista de departamentos"""
    departments = Department.objects.filter(deleted_at__isnull=True).select_related('agency', 'parent_department').order_by('agency__name', 'name')
    return render(request, 'base_tables/department_list.html', {'departments': departments})


@login_required
@user_passes_test(is_staff_user)
def department_create(request):
    """Criar novo departamento"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, _('Departamento criado com sucesso!'))
            return redirect('base_tables:department_list')
    else:
        form = DepartmentForm()
    
    return render(request, 'base_tables/department_form.html', {'form': form, 'title': _('Novo Departamento')})


@login_required
@user_passes_test(is_staff_user)
def department_edit(request, pk):
    """Editar departamento"""
    department = get_object_or_404(Department, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, _('Departamento atualizado com sucesso!'))
            return redirect('base_tables:department_list')
    else:
        form = DepartmentForm(instance=department)
    
    return render(request, 'base_tables/department_form.html', {
        'form': form, 
        'department': department, 
        'title': _('Editar Departamento')
    })


@login_required
@user_passes_test(is_staff_user)
def department_delete(request, pk):
    """Deletar departamento (soft delete)"""
    department = get_object_or_404(Department, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        department.deleted_at = timezone.now()
        department.save()
        messages.success(request, _('Departamento removido com sucesso!'))
        return redirect('base_tables:department_list')
    
    return render(request, 'base_tables/department_confirm_delete.html', {'department': department})


# ==================== AgencyUnit Views ====================

@login_required
@user_passes_test(is_staff_user)
def agency_unit_list(request):
    """Lista de unidades operacionais"""
    units = AgencyUnit.objects.filter(deleted_at__isnull=True).select_related('agency').order_by('agency__name', 'name')
    return render(request, 'base_tables/agency_unit_list.html', {'units': units})


@login_required
@user_passes_test(is_staff_user)
def agency_unit_create(request):
    """Criar nova unidade operacional"""
    if request.method == 'POST':
        form = AgencyUnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, _('Unidade operacional criada com sucesso!'))
            return redirect('base_tables:agency_unit_list')
    else:
        form = AgencyUnitForm()
    
    return render(request, 'base_tables/agency_unit_form.html', {'form': form, 'title': _('Nova Unidade Operacional')})


@login_required
@user_passes_test(is_staff_user)
def agency_unit_edit(request, pk):
    """Editar unidade operacional"""
    unit = get_object_or_404(AgencyUnit, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = AgencyUnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, _('Unidade operacional atualizada com sucesso!'))
            return redirect('base_tables:agency_unit_list')
    else:
        form = AgencyUnitForm(instance=unit)
    
    return render(request, 'base_tables/agency_unit_form.html', {
        'form': form, 
        'unit': unit, 
        'title': _('Editar Unidade Operacional')
    })


@login_required
@user_passes_test(is_staff_user)
def agency_unit_delete(request, pk):
    """Deletar unidade operacional (soft delete)"""
    unit = get_object_or_404(AgencyUnit, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        unit.deleted_at = timezone.now()
        unit.save()
        messages.success(request, _('Unidade operacional removida com sucesso!'))
        return redirect('base_tables:agency_unit_list')
    
    return render(request, 'base_tables/agency_unit_confirm_delete.html', {'unit': unit})


# ==================== EmployeePosition Views ====================

@login_required
@user_passes_test(is_staff_user)
def employee_position_list(request):
    """Lista de cargos"""
    positions = EmployeePosition.objects.filter(deleted_at__isnull=True).order_by('-default_selection', 'name')
    return render(request, 'base_tables/employee_position_list.html', {'positions': positions})


@login_required
@user_passes_test(is_staff_user)
def employee_position_create(request):
    """Criar novo cargo"""
    if request.method == 'POST':
        form = EmployeePositionForm(request.POST)
        if form.is_valid():
            position = form.save()
            messages.success(request, _('Cargo criado com sucesso!'))
            return redirect('base_tables:employee_position_list')
    else:
        form = EmployeePositionForm()
    
    return render(request, 'base_tables/employee_position_form.html', {'form': form, 'title': _('Novo Cargo')})


@login_required
@user_passes_test(is_staff_user)
def employee_position_edit(request, pk):
    """Editar cargo"""
    position = get_object_or_404(EmployeePosition, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = EmployeePositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(request, _('Cargo atualizado com sucesso!'))
            return redirect('base_tables:employee_position_list')
    else:
        form = EmployeePositionForm(instance=position)
    
    return render(request, 'base_tables/employee_position_form.html', {
        'form': form, 
        'position': position, 
        'title': _('Editar Cargo')
    })


@login_required
@user_passes_test(is_staff_user)
def employee_position_delete(request, pk):
    """Deletar cargo (soft delete)"""
    position = get_object_or_404(EmployeePosition, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        position.deleted_at = timezone.now()
        position.save()
        messages.success(request, _('Cargo removido com sucesso!'))
        return redirect('base_tables:employee_position_list')
    
    return render(request, 'base_tables/employee_position_confirm_delete.html', {'position': position})


# ==================== ProcedureCategory Views ====================

@login_required
@user_passes_test(is_staff_user)
def procedure_category_list(request):
    """Lista de categorias de procedimento"""
    categories = ProcedureCategory.objects.filter(deleted_at__isnull=True).order_by('-default_selection', 'name')
    return render(request, 'base_tables/procedure_category_list.html', {'categories': categories})


@login_required
@user_passes_test(is_staff_user)
def procedure_category_create(request):
    """Criar nova categoria de procedimento"""
    if request.method == 'POST':
        form = ProcedureCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, _('Categoria de procedimento criada com sucesso!'))
            return redirect('base_tables:procedure_category_list')
    else:
        form = ProcedureCategoryForm()
    
    return render(request, 'base_tables/procedure_category_form.html', {'form': form, 'title': _('Nova Categoria de Procedimento')})


@login_required
@user_passes_test(is_staff_user)
def procedure_category_edit(request, pk):
    """Editar categoria de procedimento"""
    category = get_object_or_404(ProcedureCategory, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = ProcedureCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _('Categoria de procedimento atualizada com sucesso!'))
            return redirect('base_tables:procedure_category_list')
    else:
        form = ProcedureCategoryForm(instance=category)
    
    return render(request, 'base_tables/procedure_category_form.html', {
        'form': form, 
        'category': category, 
        'title': _('Editar Categoria de Procedimento')
    })


@login_required
@user_passes_test(is_staff_user)
def procedure_category_delete(request, pk):
    """Deletar categoria de procedimento (soft delete)"""
    category = get_object_or_404(ProcedureCategory, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        category.deleted_at = timezone.now()
        category.save()
        messages.success(request, _('Categoria de procedimento removida com sucesso!'))
        return redirect('base_tables:procedure_category_list')
    
    return render(request, 'base_tables/procedure_category_confirm_delete.html', {'category': category})


# ==================== CrimeCategory Views ====================

@login_required
@user_passes_test(is_staff_user)
def crime_category_list(request):
    """Lista de categorias de crime"""
    categories = CrimeCategory.objects.filter(deleted_at__isnull=True).order_by('-default_selection', 'name')
    return render(request, 'base_tables/crime_category_list.html', {'categories': categories})


@login_required
@user_passes_test(is_staff_user)
def crime_category_create(request):
    """Criar nova categoria de crime"""
    if request.method == 'POST':
        form = CrimeCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, _('Categoria de crime criada com sucesso!'))
            return redirect('base_tables:crime_category_list')
    else:
        form = CrimeCategoryForm()
    
    return render(request, 'base_tables/crime_category_form.html', {'form': form, 'title': _('Nova Categoria de Crime')})


@login_required
@user_passes_test(is_staff_user)
def crime_category_edit(request, pk):
    """Editar categoria de crime"""
    category = get_object_or_404(CrimeCategory, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = CrimeCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _('Categoria de crime atualizada com sucesso!'))
            return redirect('base_tables:crime_category_list')
    else:
        form = CrimeCategoryForm(instance=category)
    
    return render(request, 'base_tables/crime_category_form.html', {
        'form': form, 
        'category': category, 
        'title': _('Editar Categoria de Crime')
    })


@login_required
@user_passes_test(is_staff_user)
def crime_category_delete(request, pk):
    """Deletar categoria de crime (soft delete)"""
    category = get_object_or_404(CrimeCategory, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        category.deleted_at = timezone.now()
        category.save()
        messages.success(request, _('Categoria de crime removida com sucesso!'))
        return redirect('base_tables:crime_category_list')
    
    return render(request, 'base_tables/crime_category_confirm_delete.html', {'category': category})


# ==================== DeviceCategory Views ====================

@login_required
@user_passes_test(is_staff_user)
def device_category_list(request):
    """Lista de categorias de dispositivo"""
    categories = DeviceCategory.objects.filter(deleted_at__isnull=True).order_by('-default_selection', 'name')
    return render(request, 'base_tables/device_category_list.html', {'categories': categories})


@login_required
@user_passes_test(is_staff_user)
def device_category_create(request):
    """Criar nova categoria de dispositivo"""
    if request.method == 'POST':
        form = DeviceCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, _('Categoria de dispositivo criada com sucesso!'))
            return redirect('base_tables:device_category_list')
    else:
        form = DeviceCategoryForm()
    
    return render(request, 'base_tables/device_category_form.html', {'form': form, 'title': _('Nova Categoria de Dispositivo')})


@login_required
@user_passes_test(is_staff_user)
def device_category_edit(request, pk):
    """Editar categoria de dispositivo"""
    category = get_object_or_404(DeviceCategory, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = DeviceCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _('Categoria de dispositivo atualizada com sucesso!'))
            return redirect('base_tables:device_category_list')
    else:
        form = DeviceCategoryForm(instance=category)
    
    return render(request, 'base_tables/device_category_form.html', {
        'form': form, 
        'category': category, 
        'title': _('Editar Categoria de Dispositivo')
    })


@login_required
@user_passes_test(is_staff_user)
def device_category_delete(request, pk):
    """Deletar categoria de dispositivo (soft delete)"""
    category = get_object_or_404(DeviceCategory, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        category.deleted_at = timezone.now()
        category.save()
        messages.success(request, _('Categoria de dispositivo removida com sucesso!'))
        return redirect('base_tables:device_category_list')
    
    return render(request, 'base_tables/device_category_confirm_delete.html', {'category': category})


# ==================== DeviceBrand Views ====================

@login_required
@user_passes_test(is_staff_user)
def device_brand_list(request):
    """Lista de marcas de dispositivo"""
    brands = DeviceBrand.objects.filter(deleted_at__isnull=True).order_by('name')
    return render(request, 'base_tables/device_brand_list.html', {'brands': brands})


@login_required
@user_passes_test(is_staff_user)
def device_brand_create(request):
    """Criar nova marca de dispositivo"""
    if request.method == 'POST':
        form = DeviceBrandForm(request.POST)
        if form.is_valid():
            brand = form.save()
            messages.success(request, _('Marca de dispositivo criada com sucesso!'))
            return redirect('base_tables:device_brand_list')
    else:
        form = DeviceBrandForm()
    
    return render(request, 'base_tables/device_brand_form.html', {'form': form, 'title': _('Nova Marca')})


@login_required
@user_passes_test(is_staff_user)
def device_brand_edit(request, pk):
    """Editar marca de dispositivo"""
    brand = get_object_or_404(DeviceBrand, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = DeviceBrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, _('Marca de dispositivo atualizada com sucesso!'))
            return redirect('base_tables:device_brand_list')
    else:
        form = DeviceBrandForm(instance=brand)
    
    return render(request, 'base_tables/device_brand_form.html', {
        'form': form, 
        'brand': brand, 
        'title': _('Editar Marca')
    })


@login_required
@user_passes_test(is_staff_user)
def device_brand_delete(request, pk):
    """Deletar marca de dispositivo (soft delete)"""
    brand = get_object_or_404(DeviceBrand, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        brand.deleted_at = timezone.now()
        brand.save()
        messages.success(request, _('Marca de dispositivo removida com sucesso!'))
        return redirect('base_tables:device_brand_list')
    
    return render(request, 'base_tables/device_brand_confirm_delete.html', {'brand': brand})


# ==================== DeviceModel Views ====================

@login_required
@user_passes_test(is_staff_user)
def device_model_list(request):
    """Lista de modelos de dispositivo"""
    models = DeviceModel.objects.filter(deleted_at__isnull=True).select_related('brand').order_by('brand__name', 'name')
    return render(request, 'base_tables/device_model_list.html', {'models': models})


@login_required
@user_passes_test(is_staff_user)
def device_model_create(request):
    """Criar novo modelo de dispositivo"""
    if request.method == 'POST':
        form = DeviceModelForm(request.POST)
        if form.is_valid():
            model = form.save()
            messages.success(request, _('Modelo de dispositivo criado com sucesso!'))
            return redirect('base_tables:device_model_list')
    else:
        form = DeviceModelForm()
    
    return render(request, 'base_tables/device_model_form.html', {'form': form, 'title': _('Novo Modelo')})


@login_required
@user_passes_test(is_staff_user)
def device_model_edit(request, pk):
    """Editar modelo de dispositivo"""
    model = get_object_or_404(DeviceModel, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = DeviceModelForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            messages.success(request, _('Modelo de dispositivo atualizado com sucesso!'))
            return redirect('base_tables:device_model_list')
    else:
        form = DeviceModelForm(instance=model)
    
    return render(request, 'base_tables/device_model_form.html', {
        'form': form, 
        'model': model, 
        'title': _('Editar Modelo')
    })


@login_required
@user_passes_test(is_staff_user)
def device_model_delete(request, pk):
    """Deletar modelo de dispositivo (soft delete)"""
    model = get_object_or_404(DeviceModel, pk=pk, deleted_at__isnull=True)
    
    if request.method == 'POST':
        model.deleted_at = timezone.now()
        model.save()
        messages.success(request, _('Modelo de dispositivo removido com sucesso!'))
        return redirect('base_tables:device_model_list')
    
    return render(request, 'base_tables/device_model_confirm_delete.html', {'model': model})
