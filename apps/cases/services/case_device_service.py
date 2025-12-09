"""
Service for CaseDevice business logic
"""
from django.db.models import Q, QuerySet
from typing import Dict, Any, Optional

from apps.core.services.base import BaseService, ValidationServiceException
from apps.cases.models import CaseDevice


class CaseDeviceService(BaseService):
    """Service for CaseDevice business logic"""
    
    model_class = CaseDevice
    
    def get_queryset(self) -> QuerySet:
        """Get CaseDevice queryset with related data"""
        return super().get_queryset().select_related(
            'case',
            'device_category',
            'device_model__brand'
        )
    
    def validate_business_rules(self, data: Dict[str, Any], instance: Optional[CaseDevice] = None) -> Dict[str, Any]:
        """Validate CaseDevice business rules"""
        
        # Coleta todos os IMEIs informados (normalizados)
        imeis = []
        for i in range(1, 6):  # imei_01 até imei_05
            imei_field = f'imei_{i:02d}'
            imei_value = data.get(imei_field)
            if imei_value:
                imei_value = str(imei_value).strip()
                if imei_value:
                    imeis.append(imei_value)
        
        # Validação 1: Verifica se há IMEI duplicado dentro do próprio dispositivo
        if len(imeis) != len(set(imeis)):
            duplicates = [imei for imei in imeis if imeis.count(imei) > 1]
            unique_duplicates = list(set(duplicates))
            raise ValidationServiceException(
                f"IMEI(s) duplicado(s) no mesmo dispositivo: {', '.join(unique_duplicates)}. "
                "Cada IMEI deve ser único dentro do dispositivo."
            )
        
        # Validação 2: Verifica se algum IMEI já existe em outro dispositivo do mesmo processo
        if imeis and data.get('case'):
            # Obtém o case (pode ser um objeto ou ID)
            case = data.get('case')
            if hasattr(case, 'pk'):
                case_id = case.pk
            elif isinstance(case, int):
                case_id = case
            else:
                # Se não conseguir obter o case, tenta usar o instance
                if instance and instance.case:
                    case_id = instance.case.pk
                else:
                    return data  # Não pode validar sem case
            
            queryset = CaseDevice.objects.filter(
                case_id=case_id,
                deleted_at__isnull=True
            )
            
            # Se estiver editando, exclui o próprio dispositivo da verificação
            if instance and instance.pk:
                queryset = queryset.exclude(pk=instance.pk)
            
            # Verifica cada IMEI informado
            for imei in imeis:
                # Verifica se o IMEI existe em qualquer campo de IMEI de outro dispositivo
                existing_device = queryset.filter(
                    Q(imei_01=imei) |
                    Q(imei_02=imei) |
                    Q(imei_03=imei) |
                    Q(imei_04=imei) |
                    Q(imei_05=imei)
                ).first()
                
                if existing_device:
                    raise ValidationServiceException(
                        f"O IMEI {imei} já está cadastrado em outro dispositivo deste processo."
                    )
        
        return data
    
    def update(self, pk: int, data: Dict[str, Any]) -> CaseDevice:
        """Update case device with version increment"""
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

