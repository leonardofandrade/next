"""
Services for extractions app
"""
from typing import Dict, Any, Optional
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.core.services.base import BaseService, ValidationServiceException, PermissionServiceException
from apps.cases.models import Extraction
from apps.core.models import ExtractorUser


class ExtractionService(BaseService):
    """Service for Extraction business logic"""
    
    model_class = Extraction
    
    def get_queryset(self) -> QuerySet:
        """Get extractions queryset with optimized queries"""
        return super().get_queryset().filter(
            case_device__deleted_at__isnull=True,
            case_device__case__deleted_at__isnull=True
        ).select_related(
            'case_device__device_category',
            'case_device__device_model__brand',
            'case_device__case',
            'assigned_to__user',
            'assigned_by',
            'started_by__user',
            'finished_by__user',
            'storage_media'
        ).order_by('-created_at')
    
    def apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply filters to queryset"""
        search = filters.get('search')
        if search:
            queryset = queryset.filter(
                Q(case_device__device_model__name__icontains=search) |
                Q(case_device__device_model__brand__name__icontains=search) |
                Q(case_device__imei_01__icontains=search) |
                Q(case_device__imei_02__icontains=search) |
                Q(case_device__imei_03__icontains=search) |
                Q(case_device__imei_04__icontains=search) |
                Q(case_device__imei_05__icontains=search) |
                Q(case_device__owner_name__icontains=search)
            )
        
        case_number = filters.get('case_number')
        if case_number:
            queryset = queryset.filter(
                case_device__case__number__icontains=case_number
            )
        
        status = filters.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        extraction_unit = filters.get('extraction_unit')
        if extraction_unit:
            queryset = queryset.filter(
                case_device__case__extraction_unit=extraction_unit
            )
        
        assigned_to = filters.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to__user=assigned_to)
        
        extraction_result = filters.get('extraction_result')
        if extraction_result:
            queryset = queryset.filter(extraction_result=extraction_result)
        
        date_from = filters.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = filters.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def get_my_extractions(self) -> QuerySet:
        """Get extractions assigned to current user"""
        if not self.user:
            raise PermissionServiceException("Usuário não autenticado")
        
        try:
            extractor_user = ExtractorUser.objects.get(
                user=self.user,
                deleted_at__isnull=True
            )
        except ExtractorUser.DoesNotExist:
            return self.model_class.objects.none()
        
        return self.get_queryset().filter(assigned_to=extractor_user)
    
    def get_extractions_by_case(self, case_pk: int) -> QuerySet:
        """Get extractions for a specific case"""
        return self.get_queryset().filter(
            case_device__case_id=case_pk
        )
    
    def get_extractor_user(self) -> ExtractorUser:
        """Get ExtractorUser for current user"""
        if not self.user:
            raise PermissionServiceException("Usuário não autenticado")
        
        try:
            return ExtractorUser.objects.get(
                user=self.user,
                deleted_at__isnull=True
            )
        except ExtractorUser.DoesNotExist:
            raise PermissionServiceException("Usuário não é um extrator")
    
    def assign_to_me(self, extraction_pk: int) -> Extraction:
        """Assign extraction to current user"""
        extraction = self.get_object(extraction_pk)
        extractor_user = self.get_extractor_user()
        
        if extraction.assigned_to == extractor_user:
            raise ValidationServiceException("Esta extração já está atribuída a você")
        
        extraction.assigned_to = extractor_user
        extraction.assigned_at = timezone.now()
        extraction.assigned_by = self.user
        
        if extraction.status == Extraction.STATUS_PENDING:
            extraction.status = Extraction.STATUS_ASSIGNED
        
        extraction.save()
        
        # Atualiza o status do Case
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def unassign_from_me(self, extraction_pk: int) -> Extraction:
        """Unassign extraction from current user"""
        extraction = self.get_object(extraction_pk)
        extractor_user = self.get_extractor_user()
        
        if extraction.assigned_to != extractor_user:
            raise PermissionServiceException(
                "Você não tem permissão para desatribuir esta extração. "
                "Apenas o responsável pode se desatribuir."
            )
        
        if extraction.status in [Extraction.STATUS_IN_PROGRESS, Extraction.STATUS_COMPLETED]:
            raise ValidationServiceException(
                "Não é possível desatribuir uma extração que já foi iniciada ou finalizada"
            )
        
        extraction.assigned_to = None
        extraction.assigned_at = None
        extraction.assigned_by = None
        
        if extraction.status == Extraction.STATUS_ASSIGNED:
            extraction.status = Extraction.STATUS_PENDING
        
        extraction.save()
        
        # Atualiza o status do Case
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def start(self, extraction_pk: int, notes: Optional[str] = None) -> Extraction:
        """Start extraction"""
        extraction = self.get_object(extraction_pk)
        extractor_user = self.get_extractor_user()
        
        if extraction.status == Extraction.STATUS_IN_PROGRESS:
            raise ValidationServiceException("Esta extração já está em andamento")
        
        if extraction.status == Extraction.STATUS_COMPLETED:
            raise ValidationServiceException(
                "Esta extração já foi finalizada e não pode ser iniciada novamente"
            )
        
        # Se não estiver atribuída, atribui automaticamente
        if not extraction.assigned_to:
            extraction.assigned_to = extractor_user
            extraction.assigned_at = timezone.now()
            extraction.assigned_by = self.user
        elif extraction.assigned_to != extractor_user:
            raise PermissionServiceException(
                f"Esta extração está atribuída a {extraction.assigned_to.user.get_full_name() or extraction.assigned_to.user.username}. "
                "Apenas o responsável pode iniciá-la."
            )
        
        extraction.status = Extraction.STATUS_IN_PROGRESS
        extraction.started_at = timezone.now()
        extraction.started_by = extractor_user
        
        if notes:
            extraction.started_notes = notes
        
        extraction.save()
        
        # Atualiza o status do Case
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def pause(self, extraction_pk: int) -> Extraction:
        """Pause extraction"""
        extraction = self.get_object(extraction_pk)
        extractor_user = self.get_extractor_user()
        
        if extraction.status != Extraction.STATUS_IN_PROGRESS:
            raise ValidationServiceException("Apenas extrações em andamento podem ser pausadas")
        
        if extraction.assigned_to != extractor_user:
            raise PermissionServiceException("Apenas o responsável pela extração pode pausá-la")
        
        extraction.status = Extraction.STATUS_PAUSED
        extraction.save()
        
        # Atualiza o status do Case
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def resume(self, extraction_pk: int) -> Extraction:
        """Resume paused extraction"""
        extraction = self.get_object(extraction_pk)
        extractor_user = self.get_extractor_user()
        
        if extraction.status != Extraction.STATUS_PAUSED:
            raise ValidationServiceException("Apenas extrações pausadas podem ser retomadas")
        
        if extraction.assigned_to != extractor_user:
            raise PermissionServiceException("Apenas o responsável pela extração pode retomá-la")
        
        extraction.status = Extraction.STATUS_IN_PROGRESS
        extraction.save()
        
        # Atualiza o status do Case
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def finish(self, extraction_pk: int, form_data: Dict[str, Any]) -> Extraction:
        """Finish extraction with form data"""
        extraction = self.get_object(extraction_pk)
        extractor_user = self.get_extractor_user()
        
        if extraction.status not in [Extraction.STATUS_IN_PROGRESS, Extraction.STATUS_PAUSED]:
            raise ValidationServiceException(
                "Apenas extrações em andamento ou pausadas podem ser finalizadas"
            )
        
        if extraction.assigned_to != extractor_user:
            raise PermissionServiceException("Apenas o responsável pela extração pode finalizá-la")
        
        # Update extraction with form data
        extraction.status = Extraction.STATUS_COMPLETED
        extraction.finished_at = timezone.now()
        extraction.finished_by = extractor_user
        
        extraction.extraction_result = form_data.get('extraction_result')
        extraction.finished_notes = form_data.get('finished_notes')
        extraction.extraction_results_notes = form_data.get('extraction_results_notes')
        
        # Tipos de extração
        extraction.logical_extraction = form_data.get('logical_extraction', False)
        extraction.logical_extraction_notes = form_data.get('logical_extraction_notes')
        extraction.physical_extraction = form_data.get('physical_extraction', False)
        extraction.physical_extraction_notes = form_data.get('physical_extraction_notes')
        extraction.full_file_system_extraction = form_data.get('full_file_system_extraction', False)
        extraction.full_file_system_extraction_notes = form_data.get('full_file_system_extraction_notes')
        extraction.cloud_extraction = form_data.get('cloud_extraction', False)
        extraction.cloud_extraction_notes = form_data.get('cloud_extraction_notes')
        
        # Cellebrite Premium
        extraction.cellebrite_premium = form_data.get('cellebrite_premium', False)
        extraction.cellebrite_premium_notes = form_data.get('cellebrite_premium_notes')
        extraction.cellebrite_premium_support = form_data.get('cellebrite_premium_support', False)
        extraction.cellebrite_premium_support_notes = form_data.get('cellebrite_premium_support_notes')
        
        # Tamanho e mídia
        if form_data.get('extraction_size'):
            extraction.extraction_size = form_data['extraction_size']
        if form_data.get('storage_media'):
            extraction.storage_media = form_data['storage_media']
        
        extraction.save()
        
        # Atualiza o status do Case
        extraction.case_device.case.update_status_based_on_extractions()
        
        return extraction
    
    def can_be_finished(self, extraction_pk: int) -> bool:
        """Check if extraction can be finished"""
        extraction = self.get_object(extraction_pk)
        extractor_user = self.get_extractor_user()
        
        if extraction.status not in [Extraction.STATUS_IN_PROGRESS, Extraction.STATUS_PAUSED]:
            return False
        
        if extraction.assigned_to != extractor_user:
            return False
        
        return True

