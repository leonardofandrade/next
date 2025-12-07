"""
Base Service Class for centralized business logic
"""
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth import get_user_model
from typing import Dict, Any, Optional, List, Union
from django.db.models import QuerySet, Model

User = get_user_model()


class ServiceException(Exception):
    """Base exception for service layer"""
    pass


class ValidationServiceException(ServiceException):
    """Exception for validation errors in service layer"""
    pass


class PermissionServiceException(ServiceException):
    """Exception for permission errors in service layer"""
    pass


class BaseService:
    """
    Base service class that provides common patterns for business logic.
    
    All business logic should be implemented in service classes to:
    1. Centralize business rules
    2. Make logic reusable between views and APIs  
    3. Enable proper testing of business logic
    4. Maintain single responsibility principle
    """
    
    model_class = None
    
    def __init__(self, user: Optional[User] = None):
        self.user = user
    
    def get_queryset(self) -> QuerySet:
        """Get base queryset for the service"""
        if self.model_class is None:
            raise NotImplementedError("model_class must be defined")
        return self.model_class.objects.filter(deleted_at__isnull=True)
    
    def get_object(self, pk: int) -> Model:
        """Get single object by ID"""
        try:
            return self.get_queryset().get(pk=pk)
        except self.model_class.DoesNotExist:
            raise ValidationServiceException(f"{self.model_class.__name__} não encontrado")
    
    def validate_permissions(self, action: str, obj: Optional[Model] = None) -> bool:
        """Validate user permissions for action"""
        # Base implementation - override in subclasses
        if self.user and hasattr(self.user, 'is_staff'):
            return self.user.is_staff or self.user.is_superuser
        return False
    
    def validate_business_rules(self, data: Dict[str, Any], instance: Optional[Model] = None) -> Dict[str, Any]:
        """Validate business rules before save/update"""
        # Base implementation - override in subclasses
        return data
    
    @transaction.atomic
    def create(self, data: Dict[str, Any]) -> Model:
        """Create new instance with business logic"""
        if not self.validate_permissions('create'):
            raise PermissionServiceException("Sem permissão para criar")
        
        validated_data = self.validate_business_rules(data)
        
        # Add created_by if user is available and model has the field
        if self.user and hasattr(self.model_class, 'created_by'):
            validated_data['created_by'] = self.user
        
        # Create instance
        instance = self.model_class(**validated_data)
        instance.save()
        
        return instance
    
    @transaction.atomic 
    def update(self, pk: int, data: Dict[str, Any]) -> Model:
        """Update instance with business logic"""
        instance = self.get_object(pk)
        
        if not self.validate_permissions('update', instance):
            raise PermissionServiceException("Sem permissão para editar")
        
        validated_data = self.validate_business_rules(data, instance)
        
        # Add updated_by if user is available and model has the field
        if self.user and hasattr(self.model_class, 'updated_by'):
            validated_data['updated_by'] = self.user
        
        # Update fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        instance.save()
        return instance
    
    @transaction.atomic
    def delete(self, pk: int) -> bool:
        """Soft delete instance"""
        instance = self.get_object(pk)
        
        if not self.validate_permissions('delete', instance):
            raise PermissionServiceException("Sem permissão para excluir")
        
        # Soft delete
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        if self.user:
            instance.deleted_by = self.user
        instance.save()
        
        return True
    
    def list_filtered(self, filters: Optional[Dict[str, Any]] = None) -> QuerySet:
        """List instances with optional filters"""
        if not self.validate_permissions('list'):
            raise PermissionServiceException("Sem permissão para listar")
            
        queryset = self.get_queryset()
        
        if filters:
            queryset = self.apply_filters(queryset, filters)
            
        return queryset
    
    def apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply filters to queryset - override in subclasses"""
        return queryset
    
    def get_user_extraction_units(self) -> List[int]:
        """
        Retorna lista de IDs das extraction_units vinculadas ao usuário.
        Retorna lista vazia se não for um extrator.
        Superusuários retornam lista vazia (sem restrição).
        """
        if not self.user or self.user.is_superuser:
            return []
        
        try:
            from apps.core.models import ExtractorUser
            
            # Busca todos os ExtractorUser vinculados ao usuário
            extractor_users = ExtractorUser.objects.filter(
                user=self.user,
                deleted_at__isnull=True
            ).prefetch_related('extraction_unit_extractors')
            
            if not extractor_users.exists():
                return []
            
            # Obtém todas as extraction_units vinculadas
            extraction_unit_ids = []
            for extractor in extractor_users:
                unit_ids = extractor.extraction_unit_extractors.filter(
                    deleted_at__isnull=True
                ).values_list('extraction_unit_id', flat=True)
                extraction_unit_ids.extend(unit_ids)
            
            return list(set(extraction_unit_ids))  # Remove duplicatas
            
        except Exception:
            return []
    
    def is_extractor_user(self) -> bool:
        """Verifica se o usuário é um extrator"""
        if not self.user or self.user.is_superuser:
            return False
        
        try:
            from apps.core.models import ExtractorUser
            return ExtractorUser.objects.filter(
                user=self.user,
                deleted_at__isnull=True
            ).exists()
        except Exception:
            return False