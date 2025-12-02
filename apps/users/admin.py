from django.contrib import admin
from django.utils.html import format_html
from apps.users.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'employee_position', 'agency_unit', 'has_image', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id', 'personal_id']
    list_filter = ['employee_position', 'agency_unit', 'theme', 'created_at']
    ordering = ['user__username']
    readonly_fields = ['created_at', 'updated_at', 'profile_image_preview']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Informações Profissionais', {
            'fields': ('agency_unit', 'employee_position', 'employee_id')
        }),
        ('Informações Pessoais', {
            'fields': ('personal_id', 'phone_number', 'mobile_number')
        }),
        ('Foto de Perfil', {
            'fields': ('profile_image_preview', 'profile_image')
        }),
        ('Preferências', {
            'fields': ('theme',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_image(self, obj):
        """Mostra se o perfil tem imagem"""
        if obj.has_profile_image:
            return format_html('<i class="fas fa-check-circle" style="color: green;"></i>')
        return format_html('<i class="fas fa-times-circle" style="color: red;"></i>')
    has_image.short_description = 'Tem Foto'
    
    def profile_image_preview(self, obj):
        """Mostra preview da imagem no admin"""
        if obj.has_profile_image:
            from django.urls import reverse
            image_url = reverse('users:profile_image', args=[obj.pk])
            return format_html(
                '<img src="{}" style="width: 150px; height: 150px; object-fit: cover; border-radius: 50%;" />',
                image_url
            )
        return "Sem imagem"
    profile_image_preview.short_description = 'Preview'
