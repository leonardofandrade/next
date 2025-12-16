"""
Services for base_tables app
"""
from typing import Dict, Any, Optional
from django.db.models import QuerySet, Model

from apps.core.services.base import BaseService
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


class BaseTableService(BaseService):
    """Base service for all base table models"""
    
    def get_queryset(self) -> QuerySet:
        """Get queryset with optimized queries"""
        queryset = super().get_queryset()
        
        # Add select_related for foreign keys if model has them
        if hasattr(self.model_class, 'organization'):
            queryset = queryset.select_related('organization')
        if hasattr(self.model_class, 'agency'):
            queryset = queryset.select_related('agency', 'agency__organization')
        if hasattr(self.model_class, 'parent_department'):
            queryset = queryset.select_related('parent_department', 'parent_department__agency')
        if hasattr(self.model_class, 'brand'):
            queryset = queryset.select_related('brand')
        
        return queryset
    
    def apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply filters to queryset"""
        # Base tables typically don't have complex filters
        # But can be extended in subclasses
        return queryset
    
    def create(self, data: Dict[str, Any]) -> Model:
        """Create instance and set created_by"""
        instance = super().create(data)
        if self.user and hasattr(instance, 'created_by'):
            instance.created_by = self.user
            instance.save(update_fields=['created_by'])
        return instance
    
    def update(self, pk: int, data: Dict[str, Any]) -> Model:
        """Update instance and set updated_by"""
        instance = super().update(pk, data)
        if self.user and hasattr(instance, 'updated_by'):
            instance.updated_by = self.user
            if hasattr(instance, 'version'):
                instance.version += 1
            instance.save(update_fields=['updated_by', 'version'] if hasattr(instance, 'version') else ['updated_by'])
        return instance


class OrganizationService(BaseTableService):
    """Service for Organization"""
    model_class = Organization
    
    def get_queryset(self) -> QuerySet:
        """Get organizations ordered by name"""
        return super().get_queryset().order_by('name')


class AgencyService(BaseTableService):
    """Service for Agency"""
    model_class = Agency
    
    def get_queryset(self) -> QuerySet:
        """Get agencies ordered by organization and name"""
        return super().get_queryset().order_by('organization__name', 'name')


class DepartmentService(BaseTableService):
    """Service for Department"""
    model_class = Department
    
    def get_queryset(self) -> QuerySet:
        """Get departments ordered by agency and name"""
        return super().get_queryset().order_by('agency__name', 'name')


class AgencyUnitService(BaseTableService):
    """Service for AgencyUnit"""
    model_class = AgencyUnit
    
    def get_queryset(self) -> QuerySet:
        """Get agency units ordered by agency and name"""
        return super().get_queryset().order_by('agency__name', 'name')


class EmployeePositionService(BaseTableService):
    """Service for EmployeePosition"""
    model_class = EmployeePosition
    
    def get_queryset(self) -> QuerySet:
        """Get employee positions ordered by default_selection and name"""
        return super().get_queryset().order_by('-default_selection', 'name')


class ProcedureCategoryService(BaseTableService):
    """Service for ProcedureCategory"""
    model_class = ProcedureCategory
    
    def get_queryset(self) -> QuerySet:
        """Get procedure categories ordered by default_selection and name"""
        return super().get_queryset().order_by('-default_selection', 'name')


class CrimeCategoryService(BaseTableService):
    """Service for CrimeCategory"""
    model_class = CrimeCategory
    
    def get_queryset(self) -> QuerySet:
        """Get crime categories ordered by default_selection and name"""
        return super().get_queryset().order_by('-default_selection', 'name')


class DocumentCategoryService(BaseTableService):
    """Service for DocumentCategory"""
    model_class = DocumentCategory
    
    def get_queryset(self) -> QuerySet:
        """Get document categories ordered by default_selection and name"""
        return super().get_queryset().order_by('-default_selection', 'name')


class DeviceCategoryService(BaseTableService):
    """Service for DeviceCategory"""
    model_class = DeviceCategory
    
    def get_queryset(self) -> QuerySet:
        """Get device categories ordered by default_selection and name"""
        return super().get_queryset().order_by('-default_selection', 'name')


class DeviceBrandService(BaseTableService):
    """Service for DeviceBrand"""
    model_class = DeviceBrand
    
    def get_queryset(self) -> QuerySet:
        """Get device brands ordered by name"""
        return super().get_queryset().order_by('name')


class DeviceModelService(BaseTableService):
    """Service for DeviceModel"""
    model_class = DeviceModel
    
    def get_queryset(self) -> QuerySet:
        """Get device models ordered by brand and name"""
        return super().get_queryset().order_by('brand__name', 'name')

