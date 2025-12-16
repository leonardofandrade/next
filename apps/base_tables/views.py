"""
Views para o app base_tables - Refatoradas usando BaseService e BaseViews
"""
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.core.mixins.views import (
    BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
)
from apps.base_tables.models import (
    Organization,
    Agency,
    Department,
    AgencyUnit,
    EmployeePosition,
    ProcedureCategory,
    CrimeCategory,
    DocumentCategory,
    DeviceCategory,
    DeviceBrand,
    DeviceModel
)
from apps.core.services.base import ServiceException
from apps.base_tables.forms import (
    OrganizationForm,
    AgencyForm,
    DepartmentForm,
    AgencyUnitForm,
    EmployeePositionForm,
    ProcedureCategoryForm,
    CrimeCategoryForm,
    DocumentCategoryForm,
    DeviceCategoryForm,
    DeviceBrandForm,
    DeviceModelForm
)
from apps.base_tables.services import (
    OrganizationService,
    AgencyService,
    DepartmentService,
    AgencyUnitService,
    EmployeePositionService,
    ProcedureCategoryService,
    CrimeCategoryService,
    DocumentCategoryService,
    DeviceCategoryService,
    DeviceBrandService,
    DeviceModelService
)


# ==================== Organization Views ====================

class OrganizationListView(BaseListView):
    """Lista de instituições"""
    model = Organization
    service_class = OrganizationService
    template_name = 'base_tables/organization_list.html'
    context_object_name = 'organizations'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organizations'] = context.get('object_list', [])
        return context


class OrganizationCreateView(BaseCreateView):
    """Criar nova instituição"""
    model = Organization
    form_class = OrganizationForm
    service_class = OrganizationService
    template_name = 'base_tables/organization_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:organization_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Instituição')
        return context
    
    def form_valid(self, form):
        """Override to use form.save() instead of service.create()"""
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Instituição criada com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class OrganizationUpdateView(BaseUpdateView):
    """Editar instituição"""
    model = Organization
    form_class = OrganizationForm
    service_class = OrganizationService
    template_name = 'base_tables/organization_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:organization_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Instituição')
        context['organization'] = self.object
        return context
    
    def form_valid(self, form):
        """Override to use form.save() instead of service.update()"""
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Instituição atualizada com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class OrganizationDeleteView(BaseDeleteView):
    """Deletar instituição (soft delete)"""
    model = Organization
    service_class = OrganizationService
    template_name = 'base_tables/organization_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:organization_list')


# ==================== Agency Views ====================

class AgencyListView(BaseListView):
    """Lista de agências"""
    model = Agency
    service_class = AgencyService
    template_name = 'base_tables/agency_list.html'
    context_object_name = 'agencies'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agencies'] = context.get('object_list', [])
        return context
    
    def get(self, request, *args, **kwargs):
        """Retorna JSON se solicitado via AJAX"""
        # Verifica se é uma requisição AJAX ou se foi solicitado formato JSON
        is_ajax = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
            request.GET.get('format') == 'json' or
            'application/json' in request.headers.get('Accept', '')
        )
        
        if is_ajax:
            # Usa o service para obter o queryset filtrado
            service = self.service_class(user=request.user)
            agencies = service.get_queryset().select_related('organization').order_by('organization__name', 'name')
            agencies_data = [{
                'id': agency.id,
                'name': agency.name,
                'acronym': agency.acronym or '',
                'organization': agency.organization.name if agency.organization else ''
            } for agency in agencies]
            return JsonResponse({'agencies': agencies_data}, safe=False)
        return super().get(request, *args, **kwargs)


class AgencyCreateView(BaseCreateView):
    """Criar nova agência"""
    model = Agency
    form_class = AgencyForm
    service_class = AgencyService
    template_name = 'base_tables/agency_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:agency_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Agência')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Agência criada com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class AgencyUpdateView(BaseUpdateView):
    """Editar agência"""
    model = Agency
    form_class = AgencyForm
    service_class = AgencyService
    template_name = 'base_tables/agency_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:agency_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Agência')
        context['agency'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Agência atualizada com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class AgencyDeleteView(BaseDeleteView):
    """Deletar agência (soft delete)"""
    model = Agency
    service_class = AgencyService
    template_name = 'base_tables/agency_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:agency_list')


# ==================== Department Views ====================

class DepartmentListView(BaseListView):
    """Lista de departamentos"""
    model = Department
    service_class = DepartmentService
    template_name = 'base_tables/department_list.html'
    context_object_name = 'departments'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = context.get('object_list', [])
        return context


class DepartmentCreateView(BaseCreateView):
    """Criar novo departamento"""
    model = Department
    form_class = DepartmentForm
    service_class = DepartmentService
    template_name = 'base_tables/department_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:department_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Novo Departamento')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Departamento criado com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class DepartmentUpdateView(BaseUpdateView):
    """Editar departamento"""
    model = Department
    form_class = DepartmentForm
    service_class = DepartmentService
    template_name = 'base_tables/department_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:department_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Departamento')
        context['department'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Departamento atualizado com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class DepartmentDeleteView(BaseDeleteView):
    """Deletar departamento (soft delete)"""
    model = Department
    service_class = DepartmentService
    template_name = 'base_tables/department_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:department_list')


# ==================== AgencyUnit Views ====================

class AgencyUnitListView(BaseListView):
    """Lista de unidades operacionais"""
    model = AgencyUnit
    service_class = AgencyUnitService
    template_name = 'base_tables/agency_unit_list.html'
    context_object_name = 'units'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['units'] = context.get('object_list', [])
        return context


class AgencyUnitCreateView(BaseCreateView):
    """Criar nova unidade operacional"""
    model = AgencyUnit
    form_class = AgencyUnitForm
    service_class = AgencyUnitService
    template_name = 'base_tables/agency_unit_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:agency_unit_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Unidade Operacional')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Unidade operacional criada com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class AgencyUnitCreateAjaxView(LoginRequiredMixin, View):
    """Criar AgencyUnit via AJAX (retorna JSON)"""
    
    def post(self, request):
        """Processa criação de AgencyUnit via AJAX"""
        form = AgencyUnitForm(request.POST)
        
        if form.is_valid():
            try:
                agency_unit = form.save(commit=False)
                agency_unit.created_by = request.user
                agency_unit.save()
                
                return JsonResponse({
                    'success': True,
                    'id': agency_unit.id,
                    'name': agency_unit.name,
                    'acronym': agency_unit.acronym or '',
                    'display_name': str(agency_unit),
                    'message': 'Unidade solicitante criada com sucesso!'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Erro ao criar unidade: {str(e)}'
                }, status=400)
        else:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({
                'success': False,
                'errors': errors,
                'error': 'Por favor, corrija os erros no formulário.'
            }, status=400)


class AgencyUnitUpdateView(BaseUpdateView):
    """Editar unidade operacional"""
    model = AgencyUnit
    form_class = AgencyUnitForm
    service_class = AgencyUnitService
    template_name = 'base_tables/agency_unit_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:agency_unit_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Unidade Operacional')
        context['unit'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Unidade operacional atualizada com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class AgencyUnitDeleteView(BaseDeleteView):
    """Deletar unidade operacional (soft delete)"""
    model = AgencyUnit
    service_class = AgencyUnitService
    template_name = 'base_tables/agency_unit_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:agency_unit_list')


# ==================== EmployeePosition Views ====================

class EmployeePositionListView(BaseListView):
    """Lista de cargos"""
    model = EmployeePosition
    service_class = EmployeePositionService
    template_name = 'base_tables/employee_position_list.html'
    context_object_name = 'positions'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['positions'] = context.get('object_list', [])
        return context


class EmployeePositionCreateView(BaseCreateView):
    """Criar novo cargo"""
    model = EmployeePosition
    form_class = EmployeePositionForm
    service_class = EmployeePositionService
    template_name = 'base_tables/employee_position_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:employee_position_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Novo Cargo')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Cargo criado com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class EmployeePositionUpdateView(BaseUpdateView):
    """Editar cargo"""
    model = EmployeePosition
    form_class = EmployeePositionForm
    service_class = EmployeePositionService
    template_name = 'base_tables/employee_position_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:employee_position_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Cargo')
        context['position'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Cargo atualizado com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class EmployeePositionDeleteView(BaseDeleteView):
    """Deletar cargo (soft delete)"""
    model = EmployeePosition
    service_class = EmployeePositionService
    template_name = 'base_tables/employee_position_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:employee_position_list')


# ==================== ProcedureCategory Views ====================

class ProcedureCategoryListView(BaseListView):
    """Lista de categorias de procedimento"""
    model = ProcedureCategory
    service_class = ProcedureCategoryService
    template_name = 'base_tables/procedure_category_list.html'
    context_object_name = 'categories'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = context.get('object_list', [])
        return context


class ProcedureCategoryCreateView(BaseCreateView):
    """Criar nova categoria de procedimento"""
    model = ProcedureCategory
    form_class = ProcedureCategoryForm
    service_class = ProcedureCategoryService
    template_name = 'base_tables/procedure_category_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:procedure_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Categoria de Procedimento')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Categoria de procedimento criada com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class ProcedureCategoryUpdateView(BaseUpdateView):
    """Editar categoria de procedimento"""
    model = ProcedureCategory
    form_class = ProcedureCategoryForm
    service_class = ProcedureCategoryService
    template_name = 'base_tables/procedure_category_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:procedure_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Categoria de Procedimento')
        context['category'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Categoria de procedimento atualizada com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class ProcedureCategoryDeleteView(BaseDeleteView):
    """Deletar categoria de procedimento (soft delete)"""
    model = ProcedureCategory
    service_class = ProcedureCategoryService
    template_name = 'base_tables/procedure_category_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:procedure_category_list')


# ==================== CrimeCategory Views ====================

class CrimeCategoryListView(BaseListView):
    """Lista de categorias de crime"""
    model = CrimeCategory
    service_class = CrimeCategoryService
    template_name = 'base_tables/crime_category_list.html'
    context_object_name = 'categories'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = context.get('object_list', [])
        return context


class CrimeCategoryCreateView(BaseCreateView):
    """Criar nova categoria de crime"""
    model = CrimeCategory
    form_class = CrimeCategoryForm
    service_class = CrimeCategoryService
    template_name = 'base_tables/crime_category_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:crime_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Categoria de Crime')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Categoria de crime criada com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class CrimeCategoryUpdateView(BaseUpdateView):
    """Editar categoria de crime"""
    model = CrimeCategory
    form_class = CrimeCategoryForm
    service_class = CrimeCategoryService
    template_name = 'base_tables/crime_category_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:crime_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Categoria de Crime')
        context['category'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Categoria de crime atualizada com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class CrimeCategoryDeleteView(BaseDeleteView):
    """Deletar categoria de crime (soft delete)"""
    model = CrimeCategory
    service_class = CrimeCategoryService
    template_name = 'base_tables/crime_category_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:crime_category_list')


# ==================== DocumentCategory Views ====================

class DocumentCategoryListView(BaseListView):
    """Lista de categorias de documento"""
    model = DocumentCategory
    service_class = DocumentCategoryService
    template_name = 'base_tables/document_category_list.html'
    context_object_name = 'categories'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = context.get('object_list', [])
        return context


class DocumentCategoryCreateView(BaseCreateView):
    """Criar nova categoria de documento"""
    model = DocumentCategory
    form_class = DocumentCategoryForm
    service_class = DocumentCategoryService
    template_name = 'base_tables/document_category_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:document_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Categoria de Documento')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Categoria de documento criada com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class DocumentCategoryUpdateView(BaseUpdateView):
    """Editar categoria de documento"""
    model = DocumentCategory
    form_class = DocumentCategoryForm
    service_class = DocumentCategoryService
    template_name = 'base_tables/document_category_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:document_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Categoria de Documento')
        context['category'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Categoria de documento atualizada com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class DocumentCategoryDeleteView(BaseDeleteView):
    """Deletar categoria de documento (soft delete)"""
    model = DocumentCategory
    service_class = DocumentCategoryService
    template_name = 'base_tables/document_category_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:document_category_list')


# ==================== DeviceCategory Views ====================

class DeviceCategoryListView(BaseListView):
    """Lista de categorias de dispositivo"""
    model = DeviceCategory
    service_class = DeviceCategoryService
    template_name = 'base_tables/device_category_list.html'
    context_object_name = 'categories'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = context.get('object_list', [])
        return context


class DeviceCategoryCreateView(BaseCreateView):
    """Criar nova categoria de dispositivo"""
    model = DeviceCategory
    form_class = DeviceCategoryForm
    service_class = DeviceCategoryService
    template_name = 'base_tables/device_category_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Categoria de Dispositivo')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Categoria de dispositivo criada com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class DeviceCategoryUpdateView(BaseUpdateView):
    """Editar categoria de dispositivo"""
    model = DeviceCategory
    form_class = DeviceCategoryForm
    service_class = DeviceCategoryService
    template_name = 'base_tables/device_category_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Categoria de Dispositivo')
        context['category'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Categoria de dispositivo atualizada com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class DeviceCategoryDeleteView(BaseDeleteView):
    """Deletar categoria de dispositivo (soft delete)"""
    model = DeviceCategory
    service_class = DeviceCategoryService
    template_name = 'base_tables/device_category_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_category_list')


# ==================== DeviceBrand Views ====================

class DeviceBrandListView(BaseListView):
    """Lista de marcas de dispositivo"""
    model = DeviceBrand
    service_class = DeviceBrandService
    template_name = 'base_tables/device_brand_list.html'
    context_object_name = 'brands'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = context.get('object_list', [])
        return context
    
    def get(self, request, *args, **kwargs):
        """Retorna JSON se for requisição AJAX"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            brands = DeviceBrand.objects.filter(deleted_at__isnull=True).order_by('name')
            brands_data = [{'id': brand.id, 'name': brand.name} for brand in brands]
            return JsonResponse({'brands': brands_data})
        return super().get(request, *args, **kwargs)


class DeviceBrandCreateView(BaseCreateView):
    """Criar nova marca de dispositivo"""
    model = DeviceBrand
    form_class = DeviceBrandForm
    service_class = DeviceBrandService
    template_name = 'base_tables/device_brand_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_brand_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Marca')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Marca de dispositivo criada com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class DeviceBrandUpdateView(BaseUpdateView):
    """Editar marca de dispositivo"""
    model = DeviceBrand
    form_class = DeviceBrandForm
    service_class = DeviceBrandService
    template_name = 'base_tables/device_brand_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_brand_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Marca')
        context['brand'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Marca de dispositivo atualizada com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class DeviceBrandCreateAjaxView(LoginRequiredMixin, View):
    """Criar DeviceBrand via AJAX (retorna JSON)"""
    
    def post(self, request):
        """Processa criação de DeviceBrand via AJAX"""
        form = DeviceBrandForm(request.POST)
        
        if form.is_valid():
            try:
                brand = form.save(commit=False)
                brand.created_by = request.user
                brand.save()
                
                return JsonResponse({
                    'success': True,
                    'id': brand.id,
                    'name': brand.name,
                    'acronym': brand.acronym or '',
                    'message': 'Marca criada com sucesso!'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Erro ao criar marca: {str(e)}'
                }, status=400)
        else:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({
                'success': False,
                'errors': errors,
                'error': 'Por favor, corrija os erros no formulário.'
            }, status=400)


class DeviceBrandDeleteView(BaseDeleteView):
    """Deletar marca de dispositivo (soft delete)"""
    model = DeviceBrand
    service_class = DeviceBrandService
    template_name = 'base_tables/device_brand_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_brand_list')


# ==================== DeviceModel Views ====================

class DeviceModelListView(BaseListView):
    """Lista de modelos de dispositivo"""
    model = DeviceModel
    service_class = DeviceModelService
    template_name = 'base_tables/device_model_list.html'
    context_object_name = 'models'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['models'] = context.get('object_list', [])
        return context


class DeviceModelCreateAjaxView(LoginRequiredMixin, View):
    """Criar DeviceModel via AJAX (retorna JSON) - Pode criar marca também"""
    
    def post(self, request):
        """Processa criação de DeviceModel via AJAX, criando marca se necessário"""
        create_new_brand = request.POST.get('create_new_brand') == 'on'
        new_brand_name = request.POST.get('new_brand_name', '').strip()
        
        brand = None
        
        # Se deve criar nova marca
        if create_new_brand:
            if not new_brand_name:
                return JsonResponse({
                    'success': False,
                    'errors': {'new_brand_name': ['Nome da marca é obrigatório.']},
                    'error': 'Por favor, informe o nome da nova marca.'
                }, status=400)
            
            # Verifica se a marca já existe (case-insensitive) antes de criar
            brand = DeviceBrand.objects.filter(
                name__iexact=new_brand_name,
                deleted_at__isnull=True
            ).first()
            
            if not brand:
                # Cria a marca apenas se não existir
                try:
                    brand = DeviceBrand.objects.create(
                        name=new_brand_name,
                        created_by=request.user
                    )
                except Exception as e:
                    # Se falhar, tenta buscar novamente (pode ter sido criado por outra requisição)
                    brand = DeviceBrand.objects.filter(
                        name__iexact=new_brand_name,
                        deleted_at__isnull=True
                    ).first()
                    
                    if not brand:
                        return JsonResponse({
                            'success': False,
                            'error': f'Erro ao criar marca: {str(e)}'
                        }, status=400)
        else:
            # Usa marca existente
            brand_id = request.POST.get('brand')
            if not brand_id:
                return JsonResponse({
                    'success': False,
                    'errors': {'brand': ['Selecione uma marca ou crie uma nova.']},
                    'error': 'Por favor, selecione uma marca ou crie uma nova.'
                }, status=400)
            
            try:
                brand = DeviceBrand.objects.get(pk=brand_id, deleted_at__isnull=True)
            except DeviceBrand.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'errors': {'brand': ['Marca não encontrada.']},
                    'error': 'Marca selecionada não encontrada.'
                }, status=400)
        
        # Cria o modelo
        form_data = request.POST.copy()
        form_data['brand'] = brand.id
        
        form = DeviceModelForm(form_data)
        
        if form.is_valid():
            try:
                # Verifica se o modelo já existe (unique_together: brand, name)
                existing_model = DeviceModel.objects.filter(
                    brand=brand,
                    name__iexact=form.cleaned_data['name'],
                    deleted_at__isnull=True
                ).first()
                
                if existing_model:
                    return JsonResponse({
                        'success': False,
                        'errors': {'name': [f'Já existe um modelo "{form.cleaned_data["name"]}" para a marca "{brand.name}".']},
                        'error': 'Este modelo já existe para esta marca.'
                    }, status=400)
                
                model = form.save(commit=False)
                model.created_by = request.user
                model.save()
                
                return JsonResponse({
                    'success': True,
                    'id': model.id,
                    'name': model.name,
                    'brand_id': model.brand.id,
                    'brand_name': model.brand.name,
                    'display_name': str(model),
                    'brand_created': create_new_brand,
                    'message': f'Modelo criado com sucesso!{" A marca também foi criada." if create_new_brand else ""}'
                })
            except Exception as e:
                # Verifica se é erro de unicidade do banco
                error_msg = str(e)
                if 'unique' in error_msg.lower() or 'duplicate' in error_msg.lower():
                    return JsonResponse({
                        'success': False,
                        'errors': {'name': ['Este modelo já existe para esta marca.']},
                        'error': 'Este modelo já existe para esta marca.'
                    }, status=400)
                
                return JsonResponse({
                    'success': False,
                    'error': f'Erro ao criar modelo: {str(e)}'
                }, status=400)
        else:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({
                'success': False,
                'errors': errors,
                'error': 'Por favor, corrija os erros no formulário.'
            }, status=400)


class DeviceModelCreateView(BaseCreateView):
    """Criar novo modelo de dispositivo"""
    model = DeviceModel
    form_class = DeviceModelForm
    service_class = DeviceModelService
    template_name = 'base_tables/device_model_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_model_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Novo Modelo')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Modelo de dispositivo criado com sucesso!'))
        return super(BaseCreateView, self).form_valid(form)


class DeviceModelUpdateView(BaseUpdateView):
    """Editar modelo de dispositivo"""
    model = DeviceModel
    form_class = DeviceModelForm
    service_class = DeviceModelService
    template_name = 'base_tables/device_model_form.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_model_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Modelo')
        context['model'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        from django.contrib import messages
        messages.success(self.request, _('Modelo de dispositivo atualizado com sucesso!'))
        return super(BaseUpdateView, self).form_valid(form)


class DeviceModelDeleteView(BaseDeleteView):
    """Deletar modelo de dispositivo (soft delete)"""
    model = DeviceModel
    service_class = DeviceModelService
    template_name = 'base_tables/device_model_confirm_delete.html'
    success_url = None
    
    def get_success_url(self):
        return reverse('base_tables:device_model_list')
