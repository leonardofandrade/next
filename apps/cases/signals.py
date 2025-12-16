"""
Signals para o app cases
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Case


@receiver(pre_save, sender=Case)
def generate_oficio_on_case_completion(sender, instance, **kwargs):
    """
    Gera ofício automaticamente quando um caso é finalizado.
    """
    # Verifica se o caso já existe no banco
    if instance.pk:
        try:
            old_instance = Case.objects.get(pk=instance.pk)
            # Verifica se o status mudou para COMPLETED e finished_at foi definido
            if (old_instance.status != Case.CASE_STATUS_COMPLETED and 
                instance.status == Case.CASE_STATUS_COMPLETED and
                instance.finished_at and
                not instance.dispatch_number):  # Só gera se ainda não tem ofício
                
                try:
                    from apps.core.services.dispatch_service import DispatchService
                    dispatch_service = DispatchService()
                    dispatch_data = dispatch_service.generate_dispatch(instance)
                    
                    # Atualiza o caso com os dados do ofício
                    instance.dispatch_number = dispatch_data['number']
                    instance.dispatch_date = dispatch_data['date']
                    instance.dispatch_file = dispatch_data['file']
                    instance.dispatch_filename = dispatch_data['filename']
                    instance.dispatch_content_type = dispatch_data['content_type']
                    
                except Exception as e:
                    # Log do erro mas não impede o salvamento
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erro ao gerar ofício para caso {instance.pk}: {str(e)}")
                    # Não levanta exceção para não impedir a finalização do caso
        except Case.DoesNotExist:
            pass
