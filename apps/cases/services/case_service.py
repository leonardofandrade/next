"""
Service for Case business logic
"""
from django.db.models import Q, QuerySet, Count
from django.utils import timezone
from typing import Dict, Any, List, Optional

from apps.core.services.base import BaseService, ValidationServiceException
from apps.cases.models import Case, Extraction


class CaseService(BaseService):
    """Service for Case business logic"""
    
    model_class = Case
    
    def get_queryset(self) -> QuerySet:
        """Get Cases queryset with related data"""
        queryset = super().get_queryset().select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category',
            'created_by',
            'assigned_to',
            'extraction_request'
        ).annotate(
            devices_count=Count('case_devices', filter=Q(case_devices__deleted_at__isnull=True))
        ).order_by('-priority', '-created_at')
        
        # Aplica filtro de extraction_unit para usuários extratores
        queryset = self._apply_extraction_unit_filter(queryset)
        
        return queryset
    
    def _apply_extraction_unit_filter(self, queryset: QuerySet) -> QuerySet:
        """
        Filtra queryset baseado nas extraction_units do usuário extrator.
        Superusuários veem todos os dados.
        """
        if not self.user or self.user.is_superuser:
            return queryset
        
        try:
            from apps.core.models import ExtractorUser
            
            # Busca todos os ExtractorUser vinculados ao usuário
            extractor_users = ExtractorUser.objects.filter(
                user=self.user,
                deleted_at__isnull=True
            ).prefetch_related('extraction_unit_extractors')
            
            if not extractor_users.exists():
                # Não é um extrator, retorna queryset completo
                return queryset
            
            # Obtém todas as extraction_units vinculadas aos extractors do usuário
            extraction_unit_ids = []
            for extractor in extractor_users:
                unit_ids = extractor.extraction_unit_extractors.filter(
                    deleted_at__isnull=True
                ).values_list('extraction_unit_id', flat=True)
                extraction_unit_ids.extend(unit_ids)
            
            if not extraction_unit_ids:
                # Extrator sem unidades vinculadas
                return queryset.none()
            
            # Filtra pelo campo extraction_unit
            return queryset.filter(extraction_unit__in=extraction_unit_ids)
            
        except Exception:
            # Em caso de erro, retorna queryset completo
            return queryset
    
    def validate_business_rules(self, data: Dict[str, Any], instance: Optional[Case] = None) -> Dict[str, Any]:
        """Validate Case business rules"""
        
        # Se estiver criando, define valores padrão
        if instance is None:
            # Set requested_at automatically if not from extraction_request
            if not data.get('requested_at'):
                data['requested_at'] = timezone.now()
            
            # Set initial status as draft
            if 'status' not in data:
                data['status'] = Case.CASE_STATUS_DRAFT
            
            # If has assigned_to, set assigned_at and assigned_by
            if data.get('assigned_to') and not data.get('assigned_at'):
                data['assigned_at'] = timezone.now()
                data['assigned_by'] = self.user
        
        # Se estiver atualizando e assigned_to mudou
        elif instance and 'assigned_to' in data:
            old_assigned_to = instance.assigned_to
            new_assigned_to = data.get('assigned_to')
            
            if old_assigned_to != new_assigned_to:
                if new_assigned_to:
                    data['assigned_at'] = timezone.now()
                    data['assigned_by'] = self.user
                else:
                    data['assigned_at'] = None
                    data['assigned_by'] = None
        
        # Validar ano obrigatório para casos não draft
        if data.get('status') != Case.CASE_STATUS_DRAFT and not data.get('year'):
            data['year'] = timezone.now().year
            
        # Validar número único por ano
        if data.get('number') and data.get('year'):
            number = data['number'] 
            year = data['year']
            
            queryset = Case.objects.filter(
                number=number, 
                year=year,
                deleted_at__isnull=True
            )
            
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
                
            if queryset.exists():
                raise ValidationServiceException(
                    f"Já existe um processo com número {number}/{year}"
                )
        
        return data
    
    def update(self, pk: int, data: Dict[str, Any]) -> Case:
        """Update case with version increment"""
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
    
    def assign_to_user(self, case_pk: int, user) -> Case:
        """Assign case to a user"""
        case = self.get_object(case_pk)
        
        if case.assigned_to == user:
            return case  # Já está atribuído
        
        # Atribui o caso ao usuário
        case.assigned_to = user
        case.assigned_at = timezone.now()
        case.assigned_by = self.user
        case.updated_by = self.user
        case.version += 1
        case.save()
        
        return case
    
    def unassign_from_user(self, case_pk: int, user) -> Case:
        """Unassign case from a user (only if assigned to that user)"""
        case = self.get_object(case_pk)
        
        # Verifica se o caso está atribuído ao usuário
        if case.assigned_to != user:
            raise ValidationServiceException(
                "Você não tem permissão para desatribuir este processo. Apenas o responsável pode se desatribuir."
            )
        
        # Remove a atribuição
        case.assigned_to = None
        case.assigned_at = None
        case.assigned_by = None
        case.updated_by = self.user
        case.version += 1
        case.save()
        
        return case
    
    def complete_registration(self, case_pk: int, create_extractions: bool = False, notes: Optional[str] = None) -> Case:
        """Complete case registration and optionally create extractions"""
        case = self.get_object(case_pk)
        
        if not self.validate_permissions('update', case):
            raise ValidationServiceException("Sem permissão para finalizar cadastro")
        
        # Check if already completed
        if case.registration_completed_at:
            raise ValidationServiceException("O cadastro deste processo já foi finalizado")
        
        # Check if has devices
        devices_count = case.case_devices.filter(deleted_at__isnull=True).count()
        if devices_count == 0:
            raise ValidationServiceException("É necessário cadastrar pelo menos um dispositivo antes de finalizar o cadastro do processo")
        
        # Check if has procedures
        procedures_count = case.procedures.filter(deleted_at__isnull=True).count()
        if procedures_count == 0:
            raise ValidationServiceException("É necessário cadastrar pelo menos um procedimento antes de finalizar o cadastro do processo")
        
        # Complete registration
        case.registration_completed_at = timezone.now()
        case.updated_by = self.user
        case.version += 1
        
        # Generate case number if not exists
        if not case.number and case.extraction_unit:
            case_number = case.generate_case_number()
            if case_number:
                case.number = case_number
                case.year = timezone.now().year
        
        # Add notes if provided
        if notes:
            if case.additional_info:
                case.additional_info += f"\n\n[Finalização de Cadastro - {timezone.now().strftime('%d/%m/%Y %H:%M')}]\n{notes}"
            else:
                case.additional_info = f"[Finalização de Cadastro - {timezone.now().strftime('%d/%m/%Y %H:%M')}]\n{notes}"
        
        # Update case status
        case.status = Case.CASE_STATUS_WAITING_EXTRACTOR
        case.save()
        
        # Create extractions if requested
        if create_extractions:
            self.create_extractions_for_case(case)
        
        return case
    
    def create_extractions_for_case(self, case: Case) -> List[Extraction]:
        """Create extractions for all devices in case that don't have extraction"""
        # Validate that case registration is completed
        if not case.registration_completed_at:
            raise ValidationServiceException(
                "Não é possível criar extrações para um caso com cadastro não finalizado. "
                "Finalize o cadastro do caso antes de criar extrações."
            )
        
        devices_without_extraction = case.case_devices.filter(
            deleted_at__isnull=True,
            device_extraction__isnull=True
        )
        extractions = []
        
        for device in devices_without_extraction:
            extraction = Extraction.objects.create(
                case_device=device,
                status=Extraction.STATUS_PENDING,
                created_by=self.user
            )
            extractions.append(extraction)
            
        # Update case status based on extractions
        case.update_status_based_on_extractions()
        
        return extractions
    
    def get_case_statistics(self, case: Case) -> Dict[str, Any]:
        """Get comprehensive case statistics"""
        devices = case.devices.filter(deleted_at__isnull=True)
        extractions = Extraction.objects.filter(
            case_device__case=case,
            deleted_at__isnull=True
        )
        
        return {
            'total_devices': devices.count(),
            'total_extractions': extractions.count(),
            'pending_extractions': extractions.filter(
                status=Extraction.EXTRACTION_STATUS_PENDING
            ).count(),
            'assigned_extractions': extractions.filter(
                status=Extraction.EXTRACTION_STATUS_ASSIGNED
            ).count(),
            'in_progress_extractions': extractions.filter(
                status=Extraction.EXTRACTION_STATUS_IN_PROGRESS
            ).count(),
            'completed_extractions': extractions.filter(
                status=Extraction.EXTRACTION_STATUS_COMPLETED
            ).count(),
            'paused_extractions': extractions.filter(
                status=Extraction.EXTRACTION_STATUS_PAUSED
            ).count(),
        }
    
    def get_my_cases(self) -> QuerySet:
        """Get cases assigned to the current user"""
        if not self.user:
            return self.model_class.objects.none()
        
        return self.get_queryset().filter(assigned_to=self.user)
    
    def apply_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply search filters to Case queryset"""
        
        if search := filters.get('search'):
            queryset = queryset.filter(
                Q(number__icontains=search) |
                Q(request_procedures__icontains=search) |
                Q(requester_authority_name__icontains=search) |
                Q(additional_info__icontains=search) |
                Q(legacy_number__icontains=search)
            )
            
        if status := filters.get('status'):
            queryset = queryset.filter(status=status)
            
        priority = filters.get('priority')
        if priority is not None and priority != '':
            queryset = queryset.filter(priority=int(priority))
            
        if requester_agency_unit := filters.get('requester_agency_unit'):
            queryset = queryset.filter(requester_agency_unit=requester_agency_unit)
            
        if extraction_unit := filters.get('extraction_unit'):
            queryset = queryset.filter(extraction_unit=extraction_unit)
            
        if assigned_to := filters.get('assigned_to'):
            queryset = queryset.filter(assigned_to=assigned_to)
            
        if crime_category := filters.get('crime_category'):
            queryset = queryset.filter(crime_category=crime_category)
            
        if date_from := filters.get('date_from'):
            queryset = queryset.filter(requested_at__date__gte=date_from)
            
        if date_to := filters.get('date_to'):
            queryset = queryset.filter(requested_at__date__lte=date_to)
            
        if year := filters.get('year'):
            queryset = queryset.filter(year=year)
            
        if created_year := filters.get('created_year'):
            queryset = queryset.filter(created_at__year=created_year)
        
        return queryset
    
    def create_case_from_requisition(self, requisition, user) -> Case:
        """
        Cria um Case a partir de uma ExtractionRequest.
        
        Args:
            requisition: Instância de ExtractionRequest
            user: Usuário que está criando o caso (para created_by)
        
        Returns:
            Case: Caso criado
        
        Raises:
            ValidationServiceException: Se a requisição já tiver um caso associado
        """
        from apps.requisitions.models import ExtractionRequest
        
        # Verifica se a requisição já tem um caso associado
        if hasattr(requisition, 'case') and requisition.case:
            raise ValidationServiceException(
                f"A requisição {requisition.id} já possui um caso associado (ID: {requisition.case.id})"
            )
        
        # Prepara os dados do caso a partir da requisição
        case_data = {
            'extraction_request': requisition,
            'requester_agency_unit': requisition.requester_agency_unit,
            'request_procedures': requisition.request_procedures,
            'crime_category': requisition.crime_category,
            'requested_device_amount': requisition.requested_device_amount,
            'requester_reply_email': requisition.requester_reply_email,
            'requester_authority_name': requisition.requester_authority_name,
            'requester_authority_position': requisition.requester_authority_position,
            'extraction_unit': requisition.extraction_unit,
            'additional_info': requisition.additional_info,
            'requested_at': requisition.requested_at or timezone.now(),
            'status': Case.CASE_STATUS_DRAFT,
            'priority': 0,  # Prioridade padrão: Baixa
            'created_by': user,
        }
        
        # Valida regras de negócio
        validated_data = self.validate_business_rules(case_data, instance=None)
        
        # Cria o caso
        case = Case.objects.create(**validated_data)
        
        return case

