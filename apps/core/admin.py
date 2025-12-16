from django.contrib import admin
from .models import DispatchSequenceNumber, DispatchTemplate


@admin.register(DispatchSequenceNumber)
class DispatchSequenceNumberAdmin(admin.ModelAdmin):
    list_display = ('extraction_unit', 'year', 'last_number', 'created_at', 'updated_at')
    list_filter = ('extraction_unit', 'year')
    search_fields = ('extraction_unit__name', 'extraction_unit__acronym')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


@admin.register(DispatchTemplate)
class DispatchTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'extraction_unit', 'is_active', 'is_default', 'created_at')
    list_filter = ('extraction_unit', 'is_active', 'is_default')
    search_fields = ('name', 'extraction_unit__name', 'extraction_unit__acronym', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('extraction_unit', 'name', 'description')
        }),
        ('Template', {
            'fields': ('template_file', 'template_filename')
        }),
        ('Status', {
            'fields': ('is_active', 'is_default')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
