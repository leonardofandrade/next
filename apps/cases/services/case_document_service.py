"""
Service for CaseDocument business logic
"""
from django.db.models import QuerySet
from typing import Dict, Any, Optional

from apps.core.services.base import BaseService
from apps.cases.models import CaseDocument


class CaseDocumentService(BaseService):
    """Service for CaseDocument business logic"""
    
    model_class = CaseDocument
    
    def get_queryset(self) -> QuerySet:
        """Get CaseDocument queryset with related data"""
        return super().get_queryset().select_related(
            'case',
            'document_category'
        )
    
    def validate_business_rules(self, data: Dict[str, Any], instance: Optional[CaseDocument] = None) -> Dict[str, Any]:
        """Validate CaseDocument business rules"""
        # Adiciona validações de negócio se necessário
        return data
    
    def update(self, pk: int, data: Dict[str, Any]) -> CaseDocument:
        """Update case document with version increment"""
        instance = self.get_object(pk)
        
        if not self.validate_permissions('update', instance):
            from apps.core.services.base import PermissionServiceException
            raise PermissionServiceException("Sem permissão para editar")
        
        validated_data = self.validate_business_rules(data, instance)
        
        # Add updated_by if user is available
        if self.user:
            validated_data['updated_by'] = self.user
        
        # Increment version
        validated_data['version'] = instance.version + 1
        
        # Update fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        instance.save()
        return instance
