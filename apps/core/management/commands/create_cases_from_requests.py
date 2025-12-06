"""
Management command para criar cases a partir de extraction_requests
"""
import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from apps.cases.models import CaseDevice
from apps.requisitions.models import ExtractionRequest
from apps.requisitions.services import ExtractionRequestService
from apps.core.services.base import ValidationServiceException
from apps.base_tables.models import DeviceCategory, DeviceModel


class Command(BaseCommand):
    help = 'Cria cases a partir de extraction_requests que ainda não possuem case vinculado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='Login/username do usuário que criará os cases (obrigatório)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Quantidade de extraction_requests a processar (opcional, se não informado processa todas)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra quais extraction_requests seriam processados sem criar os cases'
        )
        parser.add_argument(
            '--create-devices',
            action='store_true',
            help='Cria case_devices automaticamente baseado no requested_device_amount'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)
        create_devices = options.get('create_devices', False)

        # Solicita login do usuário se não foi fornecido
        if not username:
            username = input('Digite o login do usuário: ').strip()
            if not username:
                raise CommandError('Login do usuário é obrigatório.')

        # Busca o usuário
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Usuário "{username}" não encontrado.')

        self.stdout.write(
            self.style.SUCCESS(f'Usuário: {user.get_full_name() or user.username} ({user.username})')
        )

        # Busca extraction_requests sem case
        all_extraction_requests = ExtractionRequest.objects.filter(
            deleted_at__isnull=True,
            case__isnull=True
        ).select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category'
        ).order_by('requested_at')

        total_available = all_extraction_requests.count()

        # Solicita limite se não foi fornecido e há requests disponíveis
        if not limit and total_available > 0:
            try:
                limit_input = input(
                    f'\nEncontradas {total_available} extraction_request(s) sem case. '
                    f'Quantas deseja processar? (Enter para processar todas): '
                ).strip()
                if limit_input:
                    limit = int(limit_input)
                    if limit <= 0:
                        raise ValueError('O limite deve ser maior que zero.')
            except ValueError as e:
                raise CommandError(f'Valor inválido para limite: {e}')
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nOperação cancelada pelo usuário.'))
                return

        # Aplica o limite se foi informado
        if limit:
            extraction_requests = all_extraction_requests[:limit]
            total_requests = min(limit, total_available)
            if limit > total_available:
                self.stdout.write(
                    self.style.WARNING(
                        f'Aviso: Solicitado processar {limit} requests, mas apenas {total_available} estão disponíveis.'
                    )
                )
        else:
            extraction_requests = all_extraction_requests
            total_requests = total_available

        if total_requests == 0:
            self.stdout.write(
                self.style.SUCCESS('Nenhuma extraction_request sem case encontrada.')
            )
            return

        if limit and limit < total_available:
            self.stdout.write(
                f'\nSerão processadas {total_requests} de {total_available} extraction_request(s) disponíveis.\n'
            )
        else:
            self.stdout.write(f'\nProcessando {total_requests} extraction_request(s) sem case.\n')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nModo DRY-RUN: Nenhum case será criado.\n'))
            for req in extraction_requests[:20]:  # Mostra apenas os primeiros 20
                self.stdout.write(
                    f'  Request #{req.pk} - '
                    f'{req.requester_agency_unit.name if req.requester_agency_unit else "N/A"} - '
                    f'{req.requested_at.strftime("%d/%m/%Y") if req.requested_at else "N/A"} - '
                    f'{req.requested_device_amount or 0} dispositivo(s)'
                )
            if total_requests > 20:
                self.stdout.write(f'  ... e mais {total_requests - 20} requests')
            return

        # Verifica se há categorias e modelos de dispositivo (se for criar devices)
        device_categories = None
        device_models = None
        if create_devices:
            device_categories = list(DeviceCategory.objects.filter(deleted_at__isnull=True))
            if not device_categories:
                self.stdout.write(
                    self.style.WARNING(
                        'Aviso: Não há categorias de dispositivo cadastradas. '
                        'Os devices não serão criados.'
                    )
                )
                create_devices = False
            else:
                device_models = list(DeviceModel.objects.filter(deleted_at__isnull=True).select_related('brand'))
                if not device_models:
                    self.stdout.write(
                        self.style.WARNING(
                            'Aviso: Não há modelos de dispositivo cadastrados. '
                            'Os devices não serão criados.'
                        )
                    )
                    create_devices = False

        created_cases = 0
        created_procedures = 0
        created_devices = 0
        errors_list = []

        self.stdout.write(f'\nProcessando {total_requests} extraction_request(s)...\n')

        # Inicializa o service com o usuário
        request_service = ExtractionRequestService(user=user)

        for extraction_request in extraction_requests:
            try:
                # Usa o service para criar o case a partir do request
                # O service já faz: criar case, parsear procedimentos, atualizar request
                case = request_service.create_case_from_request(extraction_request.pk)
                created_cases += 1

                # Conta os procedimentos criados
                created_procedures += case.procedures.filter(deleted_at__isnull=True).count()
                
                # Cria case_devices se solicitado
                if create_devices and extraction_request.requested_device_amount and device_categories and device_models:
                    device_amount = extraction_request.requested_device_amount
                    for i in range(device_amount):
                        # Seleciona categoria e modelo aleatórios
                        device_category = random.choice(device_categories)
                        device_model = random.choice(device_models) if device_models else None

                        # Cria um dispositivo básico
                        CaseDevice.objects.create(
                            case=case,
                            device_category=device_category,
                            device_model=device_model,
                            created_by=user
                        )
                        created_devices += 1

                if created_cases % 10 == 0:
                    self.stdout.write(f'  {created_cases} cases criados...')
                
            except ValidationServiceException as e:
                # Captura erros de validação do service (ex: case já existe)
                error_msg = f'Request #{extraction_request.pk}: {str(e)}'
                errors_list.append(error_msg)
                self.stdout.write(
                    self.style.ERROR(error_msg)
                )
                continue

            except Exception as e:
                error_msg = f'Erro ao criar case para request #{extraction_request.pk}: {str(e)}'
                errors_list.append(error_msg)
                self.stdout.write(
                    self.style.ERROR(error_msg)
                )
                continue

        # Resumo final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ {created_cases} de {total_requests} case(s) criado(s) com sucesso!'
            )
        )
        
        if total_requests > created_cases:
            self.stdout.write(
                self.style.WARNING(
                    f'  ({total_requests - created_cases} case(s) falharam ao processar)'
                )
            )
        
        if created_procedures > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {created_procedures} procedimento(s) criado(s)')
            )
        
        if created_devices > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {created_devices} dispositivo(s) criado(s)')
            )

        if errors_list:
            self.stdout.write('\n' + self.style.WARNING('Avisos/Erros encontrados:'))
            for error in errors_list:
                self.stdout.write(f'  - {error}')

        self.stdout.write('='*60 + '\n')

