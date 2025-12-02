from django.contrib import admin
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


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['acronym', 'name', 'created_at']
    search_fields = ['name', 'acronym']
    list_filter = ['created_at']
    ordering = ['name']


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ['acronym', 'name', 'organization', 'created_at']
    search_fields = ['name', 'acronym', 'organization__name']
    list_filter = ['organization', 'created_at']
    ordering = ['organization__name', 'name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['acronym', 'name', 'agency', 'parent_department', 'created_at']
    search_fields = ['name', 'acronym', 'agency__name']
    list_filter = ['agency', 'created_at']
    ordering = ['agency__name', 'name']


@admin.register(AgencyUnit)
class AgencyUnitAdmin(admin.ModelAdmin):
    list_display = ['acronym', 'name', 'agency', 'city', 'phone_number', 'created_at']
    search_fields = ['name', 'acronym', 'agency__name', 'city']
    list_filter = ['agency', 'state', 'created_at']
    ordering = ['agency__name', 'name']


@admin.register(EmployeePosition)
class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'acronym', 'default_selection', 'created_at']
    search_fields = ['name', 'acronym']
    list_filter = ['default_selection', 'created_at']
    ordering = ['-default_selection', 'name']


@admin.register(ProcedureCategory)
class ProcedureCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'acronym', 'default_selection', 'created_at']
    search_fields = ['name', 'acronym']
    list_filter = ['default_selection', 'created_at']
    ordering = ['-default_selection', 'name']


@admin.register(CrimeCategory)
class CrimeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'acronym', 'default_selection', 'created_at']
    search_fields = ['name', 'acronym']
    list_filter = ['default_selection', 'created_at']
    ordering = ['-default_selection', 'name']


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'acronym', 'default_selection', 'created_at']
    search_fields = ['name', 'acronym']
    list_filter = ['default_selection', 'created_at']
    ordering = ['-default_selection', 'name']


@admin.register(DeviceBrand)
class DeviceBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'acronym', 'created_at']
    search_fields = ['name', 'acronym']
    list_filter = ['created_at']
    ordering = ['name']


@admin.register(DeviceModel)
class DeviceModelAdmin(admin.ModelAdmin):
    list_display = ['brand', 'name', 'commercial_name', 'code', 'created_at']
    search_fields = ['name', 'commercial_name', 'code', 'brand__name']
    list_filter = ['brand', 'created_at']
    ordering = ['brand__name', 'name']
