from django.contrib import admin
from .models import DispatchSequenceNumber, DocumentTemplate


@admin.register(DispatchSequenceNumber)
class DispatchSequenceNumberAdmin(admin.ModelAdmin):
    list_display = ('extraction_unit', 'year', 'last_number', 'created_at', 'updated_at')
    list_filter = ('extraction_unit', 'year')
    search_fields = ('extraction_unit__name', 'extraction_unit__acronym')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'extraction_unit', 'is_default', 'created_at')
    list_filter = ('extraction_unit', 'is_default')
    search_fields = ('name', 'extraction_unit__name', 'extraction_unit__acronym', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('extraction_unit', 'name', 'description')
        }),
        ('Cabeçalho', {
            'fields': ('header_left_logo', 'header_right_logo', 'header_text')
        }),
        ('Conteúdo', {
            'fields': ('subject_text', 'body_text', 'signature_text')
        }),
        ('Rodapé e Água-Marinha', {
            'fields': ('footer_left_logo', 'footer_right_logo', 'footer_text', 'watermark_text', 'watermark_logo')
        }),
        ('Status', {
            'fields': ('is_default',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
