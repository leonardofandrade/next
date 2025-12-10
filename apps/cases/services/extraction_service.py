"""
Service for Extraction business logic
"""
from django.db.models import Q, QuerySet
from django.utils import timezone
from typing import Dict, Any

from apps.core.services.base import BaseService, ValidationServiceException
from apps.cases.models import Extraction


class ExtractionService(BaseService):
    """Service for Extraction business logic"""
    
    model_class = Extraction
    
    def get_queryset(self) -> QuerySet:
        """Get Extraction queryset with related data"""
        return super().get_queryset().select_related(
            'case_device__case',
            'case_device__device_category',
            'case_device__device_model__brand',
            'assigned_to__user',
            'assigned_by',
            'started_by__user',
            'finished_by__user',
            'storage_media'
        )
    
    def assign_extraction(self, extraction_pk: int, extractor_user_pk: int) -> Extraction:
        """Assign extraction to extractor"""
        from apps.core.models import ExtractorUser
        
        extraction = self.get_object(extraction_pk)
        extractor_user = ExtractorUser.objects.get(
            pk=extractor_user_pk, 
            deleted_at__isnull=True
        )
        
        if extraction.status != Extraction.EXTRACTION_STATUS_PENDING:
            raise ValidationServiceException("Extração deve estar pendente para ser atribuída")
            
        extraction.assigned_to = extractor_user
        extraction.assigned_by = self.user
        extraction.status = Extraction.EXTRACTION_STATUS_ASSIGNED
        # updated_by será preenchido automaticamente pelo AuditedModel.save()
        extraction.save()
        
        # Update case status
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def start_extraction(self, extraction_pk: int) -> Extraction:
        """Start extraction"""
        extraction = self.get_object(extraction_pk)
        
        if extraction.status != Extraction.EXTRACTION_STATUS_ASSIGNED:
            raise ValidationServiceException("Extração deve estar atribuída para ser iniciada")
            
        extraction.status = Extraction.EXTRACTION_STATUS_IN_PROGRESS
        extraction.started_at = timezone.now()
        extraction.started_by = extraction.assigned_to
        # updated_by será preenchido automaticamente pelo AuditedModel.save()
        extraction.save()
        
        # Update case status
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def pause_extraction(self, extraction_pk: int, reason: str = "") -> Extraction:
        """Pause extraction"""
        extraction = self.get_object(extraction_pk)
        
        if extraction.status != Extraction.EXTRACTION_STATUS_IN_PROGRESS:
            raise ValidationServiceException("Extração deve estar em progresso para ser pausada")
            
        extraction.status = Extraction.EXTRACTION_STATUS_PAUSED
        extraction.pause_reason = reason
        # updated_by será preenchido automaticamente pelo AuditedModel.save()
        extraction.save()
        
        # Update case status  
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def complete_extraction(self, extraction_pk: int, **kwargs) -> Extraction:
        """Complete extraction"""
        extraction = self.get_object(extraction_pk)
        
        valid_statuses = [
            Extraction.EXTRACTION_STATUS_IN_PROGRESS,
            Extraction.EXTRACTION_STATUS_PAUSED
        ]
        
        if extraction.status not in valid_statuses:
            raise ValidationServiceException("Extração deve estar em progresso ou pausada para ser finalizada")
            
        extraction.status = Extraction.EXTRACTION_STATUS_COMPLETED
        extraction.finished_at = timezone.now()
        extraction.finished_by = extraction.assigned_to
        
        # Update optional fields
        for field, value in kwargs.items():
            if hasattr(extraction, field):
                setattr(extraction, field, value)
        
        # updated_by será preenchido automaticamente pelo AuditedModel.save()
        extraction.save()
        
        # Update case status
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply search filters to Extraction queryset"""
        
        if search := filters.get('search'):
            queryset = queryset.filter(
                Q(case_device__device_model__name__icontains=search) |
                Q(case_device__imei__icontains=search) |
                Q(case_device__owner_name__icontains=search) |
                Q(case_device__case__number__icontains=search)
            )
            
        if status := filters.get('status'):
            queryset = queryset.filter(status=status)
            
        if case_pk := filters.get('case'):
            queryset = queryset.filter(case_device__case_id=case_pk)
            
        if assigned_to := filters.get('assigned_to'):
            queryset = queryset.filter(assigned_to_id=assigned_to)
            
        return queryset

