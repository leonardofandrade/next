import sys
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.models import User
from apps.cases.models import Case, CaseProcedure, CaseDevice, Extraction
from apps.requisitions.models import ExtractionRequest


class Command(BaseCommand):
    help = "Remove todos os casos (Case) e dados relacionados do banco de dados"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Executa a remoção sem confirmação interativa',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra quais registros seriam removidos sem executar a remoção',
        )
        parser.add_argument(
            '--status',
            type=str,
            help='Remove apenas casos com status específico (ex: incomplete, finished)',
        )
        parser.add_argument(
            '--older-than-days',
            type=int,
            help='Remove apenas casos criados há mais de X dias',
        )
        parser.add_argument(
            '--created-by',
            type=str,
            help='Remove apenas casos criados por um usuário específico',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        status_filter = options.get('status')
        older_than_days = options.get('older_than_days')
        created_by = options.get('created_by')

        # Coletar estatísticas antes da remoção
        stats = self._collect_statistics(status_filter, older_than_days, created_by)
        
        if stats['total_cases'] == 0:
            self.stdout.write(
                self.style.SUCCESS("Nenhum caso encontrado para remoção.")
            )
            return

        # Mostrar estatísticas
        self._display_statistics(stats)

        # Se for dry-run, apenas mostrar o que seria removido
        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n🔍 MODO DRY-RUN: Nenhum dado foi removido.")
            )
            return

        # Confirmação interativa (a menos que --force seja usado)
        if not force:
            if not self._confirm_deletion(stats):
                self.stdout.write(
                    self.style.WARNING("Operação cancelada pelo usuário.")
                )
                return

        # Executar remoção
        try:
            with transaction.atomic():
                deleted_counts = self._delete_cases(stats['queryset'])
                self._display_results(deleted_counts)
        except Exception as e:
            raise CommandError(f"Erro durante a remoção: {str(e)}")

    def _collect_statistics(self, status_filter, older_than_days, created_by):
        """Coleta estatísticas dos casos que serão removidos"""
        from django.utils import timezone
        from datetime import timedelta

        # Base queryset
        cases_qs = Case.objects.all()
        
        # Aplicar filtros
        if status_filter:
            cases_qs = cases_qs.filter(status=status_filter)
        
        if older_than_days:
            cutoff_date = timezone.now() - timedelta(days=older_than_days)
            cases_qs = cases_qs.filter(created_at__lt=cutoff_date)
        
        if created_by:
            try:
                user = User.objects.get(username=created_by)
                cases_qs = cases_qs.filter(created_by=user)
            except User.DoesNotExist:
                raise CommandError(f"Usuário '{created_by}' não encontrado")

        # Contar registros relacionados
        total_cases = cases_qs.count()
        total_documents = CaseProcedure.objects.filter(case__in=cases_qs).count()
        total_devices = CaseDevice.objects.filter(case__in=cases_qs).count()
        # Contar extrações (serão removidas automaticamente quando CaseDevice for removido)
        total_extractions = Extraction.objects.filter(case_device__case__in=cases_qs).count()
        # Contar extraction_requests que serão revertidas
        # O relacionamento é OneToOneField do Case para ExtractionRequest com related_name='case'
        total_requests = ExtractionRequest.objects.filter(case__id__in=cases_qs.values_list('id', flat=True)).count()

        # Estatísticas por status
        status_stats = {}
        for case in cases_qs.values('status').distinct():
            status = case['status']
            count = cases_qs.filter(status=status).count()
            status_stats[status] = count

        return {
            'queryset': cases_qs,
            'total_cases': total_cases,
            'total_documents': total_documents,
            'total_devices': total_devices,
            'total_extractions': total_extractions,
            'total_requests': total_requests,
            'status_stats': status_stats
        }

    def _display_statistics(self, stats):
        """Exibe estatísticas dos dados que serão removidos"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 ESTATÍSTICAS DE REMOÇÃO")
        self.stdout.write("="*60)
        
        self.stdout.write(f"📋 Casos: {stats['total_cases']}")
        self.stdout.write(f"📄 Procedimentos: {stats['total_documents']}")
        self.stdout.write(f"📱 Dispositivos: {stats['total_devices']}")
        if stats['total_extractions'] > 0:
            self.stdout.write(f"🔬 Extrações (removidas automaticamente): {stats['total_extractions']}")
        if stats['total_requests'] > 0:
            self.stdout.write(f"📝 Solicitações de extração que serão revertidas: {stats['total_requests']}")
        
        if stats['status_stats']:
            self.stdout.write("\n📈 Por Status:")
            for status, count in stats['status_stats'].items():
                status_display = dict(Case.CASE_STATUS_CHOICES).get(status, status)
                self.stdout.write(f"   • {status_display}: {count}")

    def _confirm_deletion(self, stats):
        """Solicita confirmação do usuário"""
        self.stdout.write("\n" + "⚠️" * 20)
        self.stdout.write("⚠️  ATENÇÃO: OPERAÇÃO IRREVERSÍVEL  ⚠️")
        self.stdout.write("⚠️" * 20)
        self.stdout.write(f"\nVocê está prestes a remover:")
        self.stdout.write(f"   • {stats['total_cases']} casos")
        self.stdout.write(f"   • {stats['total_documents']} procedimentos")
        self.stdout.write(f"   • {stats['total_devices']} dispositivos")
        if stats['total_extractions'] > 0:
            self.stdout.write(f"   • {stats['total_extractions']} extrações (removidas automaticamente)")
        if stats['total_requests'] > 0:
            self.stdout.write(f"   • {stats['total_requests']} solicitações de extração terão o status revertido")
        self.stdout.write("\nEsta operação é IRREVERSÍVEL!")
        
        while True:
            response = input("\nDigite 'CONFIRMAR' para prosseguir ou 'cancelar' para abortar: ").strip()
            if response == 'CONFIRMAR':
                return True
            elif response.lower() in ['cancelar', 'cancel', 'n', 'no']:
                return False
            else:
                self.stdout.write("Resposta inválida. Digite 'CONFIRMAR' ou 'cancelar'.")

    def _delete_cases(self, cases_qs):
        """Executa a remoção dos casos e dados relacionados"""
        deleted_counts = {
            'cases': 0,
            'documents': 0,
            'devices': 0,
            'requests_reverted': 0
        }

        # Obter IDs dos casos antes da remoção para contar procedimentos e dispositivos
        case_ids = list(cases_qs.values_list('id', flat=True))
        
        # Contar procedimentos e dispositivos que serão removidos
        deleted_counts['documents'] = CaseProcedure.objects.filter(case_id__in=case_ids).count()
        deleted_counts['devices'] = CaseDevice.objects.filter(case_id__in=case_ids).count()

        # Reverter status das ExtractionRequests associadas antes de remover os cases
        # O relacionamento é OneToOneField do Case para ExtractionRequest com related_name='case'
        requests_to_revert = ExtractionRequest.objects.filter(case__id__in=case_ids)
        if requests_to_revert.exists():
            requests_reverted = requests_to_revert.update(
                status=ExtractionRequest.REQUEST_STATUS_ASSIGNED,
                received_at=None,
                received_by=None,
                receipt_notes=None
            )
            deleted_counts['requests_reverted'] = requests_reverted
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {requests_reverted} solicitação(ões) de extração revertida(s) para status 'Aguardando Material'"
                )
            )

        # IMPORTANTE: Remover CaseDevices primeiro devido ao PROTECT
        # CaseDevices têm on_delete=models.PROTECT, então devem ser removidos manualmente
        devices_deleted = CaseDevice.objects.filter(case_id__in=case_ids).delete()[0]
        deleted_counts['devices'] = devices_deleted
        
        # Remover procedimentos (PROTECT, então devem ser removidos manualmente)
        documents_deleted = CaseProcedure.objects.filter(case_id__in=case_ids).delete()[0]
        deleted_counts['documents'] = documents_deleted

        # Agora remover os casos (sem mais restrições de chave estrangeira)
        cases_deleted = cases_qs.delete()[0]
        deleted_counts['cases'] = cases_deleted

        return deleted_counts

    def _display_results(self, deleted_counts):
        """Exibe os resultados da remoção"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("✅ REMOÇÃO CONCLUÍDA COM SUCESSO!")
        self.stdout.write("="*60)
        self.stdout.write(f"🗑️  Casos removidos: {deleted_counts['cases']}")
        self.stdout.write(f"🗑️  Procedimentos removidos: {deleted_counts['documents']}")
        self.stdout.write(f"🗑️  Dispositivos removidos: {deleted_counts['devices']}")
        if deleted_counts['requests_reverted'] > 0:
            self.stdout.write(f"🔄 Solicitações de extração revertidas: {deleted_counts['requests_reverted']}")
        self.stdout.write("\n🎉 Limpeza de dados concluída!")
