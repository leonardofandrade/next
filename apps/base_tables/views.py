"""
Views para o app base_tables - Refatoradas usando BaseService e BaseViews
"""
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

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
from apps.base_tables.services import (
    OrganizationService,
    AgencyService,
    DepartmentService,
    AgencyUnitService,
    EmployeePositionService,
    ProcedureCategoryService,
    CrimeCategoryService,
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
