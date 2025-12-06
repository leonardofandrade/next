"""
Management command para completar cases com cadastro incompleto
Gera dados de teste para preencher informações faltantes e finaliza o cadastro
"""
import random
import re
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from faker import Faker

from apps.cases.models import Case, CaseDevice, CaseProcedure
from apps.cases.services import CaseService, CaseDeviceService
from apps.core.services.base import ValidationServiceException
from apps.base_tables.models import DeviceCategory, DeviceModel, ProcedureCategory


class Command(BaseCommand):
    help = 'Completa cases com cadastro incompleto, preenchendo dados faltantes e finalizando o cadastro'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='Login/username do usuário que processará os cases (opcional, usa o primeiro usuário se não informado)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Quantidade máxima de cases a processar (opcional, se não informado processa todos)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra quais cases seriam processados sem fazer alterações'
        )
        parser.add_argument(
            '--skip-devices',
            action='store_true',
            help='Não cria devices se não existirem (apenas completa dados existentes)'
        )
        parser.add_argument(
            '--skip-procedures',
            action='store_true',
            help='Não cria procedures se não existirem (apenas completa dados existentes)'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)
        skip_devices = options.get('skip_devices', False)
        skip_procedures = options.get('skip_procedures', False)

        # Busca o usuário
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f'Usuário "{username}" não encontrado.')
        else:
            user = User.objects.first()
            if not user:
                raise CommandError('Nenhum usuário encontrado no sistema.')
            self.stdout.write(
                self.style.WARNING(f'Usando usuário: {user.username} (use --username para especificar)')
            )

        # Busca cases com cadastro incompleto
        incomplete_cases = Case.objects.filter(
            deleted_at__isnull=True,
            registration_completed_at__isnull=True
        ).annotate(
            devices_count=Count('case_devices', filter=Q(case_devices__deleted_at__isnull=True)),
            procedures_count=Count('procedures', filter=Q(procedures__deleted_at__isnull=True))
        ).select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category'
        )

        total_cases = incomplete_cases.count()

        if total_cases == 0:
            self.stdout.write(
                self.style.SUCCESS('Nenhum case com cadastro incompleto encontrado.')
            )
            return

        # Aplica limite se fornecido
        if limit:
            incomplete_cases = incomplete_cases[:limit]
            total_to_process = min(limit, total_cases)
        else:
            total_to_process = total_cases

        self.stdout.write(f'Encontrados {total_cases} cases com cadastro incompleto.')
        if limit:
            self.stdout.write(f'Processando {total_to_process} de {total_cases} cases.')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nModo DRY-RUN: Nenhuma alteração será feita.\n'))
            for case in incomplete_cases[:10]:
                devices_count = case.devices_count or 0
                procedures_count = case.procedures_count or 0
                self.stdout.write(
                    f'  Case #{case.pk} - {case.number or "Sem número"} - '
                    f'Devices: {devices_count}, Procedures: {procedures_count}'
                )
            if total_to_process > 10:
                self.stdout.write(f'  ... e mais {total_to_process - 10} cases')
            return

        # Verifica dados necessários
        device_categories = list(DeviceCategory.objects.filter(deleted_at__isnull=True))
        device_models = list(DeviceModel.objects.filter(deleted_at__isnull=True).select_related('brand'))
        procedure_categories = list(ProcedureCategory.objects.filter(deleted_at__isnull=True))

        if not device_categories and not skip_devices:
            self.stdout.write(
                self.style.WARNING('Aviso: Não há categorias de dispositivo cadastradas.')
            )
        if not device_models and not skip_devices:
            self.stdout.write(
                self.style.WARNING('Aviso: Não há modelos de dispositivo cadastrados.')
            )
        if not procedure_categories and not skip_procedures:
            self.stdout.write(
                self.style.WARNING('Aviso: Não há categorias de procedimento cadastradas.')
            )

        # Inicializa Faker
        fake = Faker('pt_BR')

        # Inicializa services
        case_service = CaseService(user=user)
        device_service = CaseDeviceService(user=user)

        # Estatísticas
        processed_cases = 0
        completed_cases = 0
        created_devices = 0
        created_procedures = 0
        errors_list = []

        # Cores e opções para devices
        colors = ['Preto', 'Branco', 'Prata', 'Dourado', 'Azul', 'Vermelho', 'Rosa', 'Verde', 'Cinza']
        storage_options = [16, 32, 64, 128, 256, 512, 1024]
        password_types = ['pin', 'password', 'pattern', 'bio', 'none']

        self.stdout.write(f'\nProcessando {total_to_process} cases...\n')

        for case in incomplete_cases:
            try:
                devices_count = case.devices_count or 0
                procedures_count = case.procedures_count or 0
                needs_devices = devices_count == 0 and not skip_devices
                needs_procedures = procedures_count == 0 and not skip_procedures

                # Cria devices se necessário
                if needs_devices and device_categories and device_models:
                    device_amount = case.requested_device_amount or 1
                    for i in range(device_amount):
                        device_data = self._generate_device_data(
                            case, device_categories, device_models, 
                            colors, storage_options, password_types, fake
                        )
                        device_service.create(device_data)
                        created_devices += 1

                # Cria procedures se necessário
                if needs_procedures and procedure_categories:
                    # Tenta parsear request_procedures primeiro
                    if case.request_procedures:
                        created = self._create_procedures_from_text(
                            case, case.request_procedures, procedure_categories, user
                        )
                        created_procedures += created
                    
                    # Se ainda não tem procedures, cria um genérico
                    if case.procedures.filter(deleted_at__isnull=True).count() == 0:
                        procedure_cat = random.choice(procedure_categories)
                        year = timezone.now().year
                        proc_number = f"{random.randint(1, 9999):04d}/{year}"
                        
                        CaseProcedure.objects.create(
                            case=case,
                            number=proc_number,
                            procedure_category=procedure_cat,
                            created_by=user
                        )
                        created_procedures += 1

                # Finaliza o cadastro usando o service
                try:
                    case_service.complete_registration(
                        case.pk,
                        create_extractions=False,
                        notes="Cadastro completado automaticamente via command de teste"
                    )
                    completed_cases += 1
                    processed_cases += 1
                    
                    if processed_cases % 10 == 0:
                        self.stdout.write(f'  {processed_cases}/{total_to_process} cases processados...')
                        
                except ValidationServiceException as e:
                    # Se ainda faltar algo, adiciona aos erros mas continua
                    error_msg = f'Case #{case.pk}: {str(e)}'
                    errors_list.append(error_msg)
                    self.stdout.write(self.style.WARNING(f'  {error_msg}'))
                    continue

            except Exception as e:
                error_msg = f'Erro ao processar case #{case.pk}: {str(e)}'
                errors_list.append(error_msg)
                self.stdout.write(self.style.ERROR(f'  {error_msg}'))
                continue

        # Resumo final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ {completed_cases} de {total_to_process} case(s) completado(s) com sucesso!'
            )
        )
        
        if processed_cases < total_to_process:
            self.stdout.write(
                self.style.WARNING(
                    f'  ({total_to_process - processed_cases} case(s) não puderam ser completados)'
                )
            )
        
        if created_devices > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {created_devices} dispositivo(s) criado(s)')
            )
        
        if created_procedures > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {created_procedures} procedimento(s) criado(s)')
            )

        if errors_list:
            self.stdout.write('\n' + self.style.WARNING('Avisos/Erros encontrados:'))
            for error in errors_list[:20]:  # Mostra apenas os primeiros 20
                self.stdout.write(f'  - {error}')
            if len(errors_list) > 20:
                self.stdout.write(f'  ... e mais {len(errors_list) - 20} erros')

        self.stdout.write('='*60 + '\n')

    def _generate_device_data(self, case, device_categories, device_models, colors, storage_options, password_types, fake):
        """Gera dados aleatórios para um device"""
        device_category = random.choice(device_categories)
        device_model = random.choice(device_models)
        
        # Gera cor aleatória (70% de chance)
        color = random.choice(colors) if random.random() > 0.3 else None
        
        # Gera IMEI (80% de chance de ter IMEI conhecido)
        is_imei_unknown = random.random() < 0.2
        imei_01 = None
        imei_02 = None
        
        if not is_imei_unknown:
            imei_01 = ''.join([str(random.randint(0, 9)) for _ in range(15)])
            if random.random() < 0.3:
                imei_02 = ''.join([str(random.randint(0, 9)) for _ in range(15)])
        
        # Gera nome do proprietário (60% de chance)
        owner_name = fake.name() if random.random() > 0.4 else None
        
        # Gera armazenamento interno (70% de chance)
        internal_storage = random.choice(storage_options) if random.random() > 0.3 else None
        
        # Status do dispositivo
        is_turned_on = random.choice([True, False, None])
        is_locked = random.choice([True, False, None]) if is_turned_on else None
        
        # Informações de senha
        is_password_known = None
        password_type = None
        password = None
        
        if is_locked:
            is_password_known = random.choice([True, False])
            if is_password_known:
                password_type = random.choice(password_types)
                if password_type != 'none':
                    if password_type == 'pin':
                        password = ''.join([str(random.randint(0, 9)) for _ in range(4, 7)])
                    elif password_type == 'pattern':
                        password = 'Padrão'
                    elif password_type == 'bio':
                        password = 'Biometria'
                    else:
                        password = fake.password(length=random.randint(4, 12))
        
        # Condição física
        is_damaged = random.choice([True, False]) if random.random() > 0.5 else None
        damage_description = None
        if is_damaged:
            damage_options = [
                'Tela trincada', 'Tela quebrada', 'Arranhões na tela',
                'Carcaça danificada', 'Botões não funcionam', 'Bateria inchada'
            ]
            damage_description = random.choice(damage_options)
        
        # Fluidos (10% de chance)
        has_fluids = random.random() < 0.1
        fluids_description = None
        if has_fluids:
            fluid_options = ['Água', 'Sangue', 'Óleo', 'Outro líquido']
            fluids_description = random.choice(fluid_options)
        
        # Acessórios
        has_sim_card = random.choice([True, False])
        sim_card_info = None
        if has_sim_card:
            sim_card_info = f'Operadora: {random.choice(["Vivo", "Claro", "TIM", "Oi"])}'
        
        has_memory_card = random.choice([True, False])
        memory_card_info = None
        if has_memory_card:
            memory_card_info = f'{random.choice([16, 32, 64, 128])} GB'
        
        has_other_accessories = random.choice([True, False])
        other_accessories_info = None
        if has_other_accessories:
            accessory_options = [
                'Capa protetora', 'Carregador', 'Fone de ouvido',
                'Cabo USB', 'Película de vidro', 'Suporte para carro'
            ]
            other_accessories_info = random.choice(accessory_options)
        
        # Lacre (40% de chance)
        is_sealed = random.random() < 0.4
        security_seal = None
        if is_sealed:
            security_seal = f'LACRE-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}'
        
        # Informações adicionais (30% de chance)
        additional_info = None
        if random.random() < 0.3:
            additional_info = fake.text(max_nb_chars=200)
        
        # Prepara dados do dispositivo
        device_data = {
            'case': case,
            'device_category': device_category,
            'device_model': device_model,
        }
        
        # Adiciona campos opcionais apenas se não forem None
        optional_fields = {
            'color': color,
            'is_imei_unknown': is_imei_unknown,
            'imei_01': imei_01,
            'imei_02': imei_02,
            'owner_name': owner_name,
            'internal_storage': internal_storage,
            'is_turned_on': is_turned_on,
            'is_locked': is_locked,
            'is_password_known': is_password_known,
            'password_type': password_type,
            'password': password,
            'is_damaged': is_damaged,
            'damage_description': damage_description,
            'has_fluids': has_fluids,
            'fluids_description': fluids_description,
            'has_sim_card': has_sim_card,
            'sim_card_info': sim_card_info,
            'has_memory_card': has_memory_card,
            'memory_card_info': memory_card_info,
            'has_other_accessories': has_other_accessories,
            'other_accessories_info': other_accessories_info,
            'is_sealed': is_sealed,
            'security_seal': security_seal,
            'additional_info': additional_info,
        }
        
        for key, value in optional_fields.items():
            if value is not None:
                device_data[key] = value
        
        return device_data

    def _create_procedures_from_text(self, case, request_procedures_text, procedure_categories, user):
        """Tenta criar procedures a partir do texto request_procedures"""
        created = 0
        if not request_procedures_text:
            return created
        
        procedures_text = request_procedures_text.strip()
        if not procedures_text:
            return created
        
        # Tenta dividir por vírgula ou ponto e vírgula
        procedures_list = re.split(r'[,;]', procedures_text)
        
        for procedure_text in procedures_list:
            procedure_text = procedure_text.strip()
            if not procedure_text:
                continue
            
            # Tenta extrair o acrônimo e o número
            match = re.match(r'^([A-Z]{1,10})\s+([0-9/]+)', procedure_text, re.IGNORECASE)
            if not match:
                match = re.match(r'^([A-Z]{1,10})', procedure_text, re.IGNORECASE)
                if match:
                    acronym = match.group(1).upper()
                    procedure_number = procedure_text.replace(acronym, '').strip()
                else:
                    continue
            else:
                acronym = match.group(1).upper()
                procedure_number = match.group(2).strip()
            
            # Busca ProcedureCategory pelo acronym
            procedure_category = None
            for proc_cat in procedure_categories:
                if proc_cat.acronym.upper() == acronym:
                    procedure_category = proc_cat
                    break
            
            if not procedure_category:
                continue
            
            # Cria o CaseProcedure
            try:
                CaseProcedure.objects.create(
                    case=case,
                    number=procedure_number if procedure_number else None,
                    procedure_category=procedure_category,
                    created_by=user
                )
                created += 1
            except Exception:
                continue
        
        return created

