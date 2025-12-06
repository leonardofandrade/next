"""
Management command para gerar dispositivos aleatórios para cases sem dispositivos
"""
import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db.models import Count
from faker import Faker

from apps.cases.models import Case
from apps.cases.services import CaseDeviceService
from apps.base_tables.models import DeviceCategory, DeviceModel


class Command(BaseCommand):
    help = 'Gera dispositivos aleatórios para cases que não possuem dispositivos cadastrados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='Login/username do usuário que criará os dispositivos (opcional, usa o primeiro usuário se não informado)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra quais cases seriam processados sem criar os dispositivos'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        dry_run = options.get('dry_run', False)

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

        # Verifica se existem dados necessários
        device_categories = list(DeviceCategory.objects.filter(deleted_at__isnull=True))
        if not device_categories:
            raise CommandError('Não há categorias de dispositivo cadastradas.')

        device_models = list(DeviceModel.objects.filter(deleted_at__isnull=True).select_related('brand'))
        if not device_models:
            raise CommandError('Não há modelos de dispositivo cadastrados.')

        # Busca cases sem dispositivos
        cases_without_devices = Case.objects.filter(
            deleted_at__isnull=True
        ).annotate(
            device_count=Count('case_devices')
        ).filter(
            device_count=0,
            requested_device_amount__gt=0
        ).select_related(
            'requester_agency_unit',
            'extraction_unit'
        )

        total_cases = cases_without_devices.count()

        if total_cases == 0:
            self.stdout.write(
                self.style.SUCCESS('Nenhum case sem dispositivos encontrado.')
            )
            return

        self.stdout.write(f'Encontrados {total_cases} cases sem dispositivos.')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nModo DRY-RUN: Nenhum dispositivo será criado.\n'))
            for case in cases_without_devices[:10]:  # Mostra apenas os primeiros 10
                self.stdout.write(
                    f'  Case #{case.pk} - {case.number or "Rascunho"} - '
                    f'{case.requested_device_amount} dispositivo(s) solicitado(s)'
                )
            if total_cases > 10:
                self.stdout.write(f'  ... e mais {total_cases - 10} cases')
            return

        # Inicializa Faker
        fake = Faker('pt_BR')

        # Cores comuns para dispositivos
        colors = [
            'Preto', 'Branco', 'Prata', 'Dourado', 'Azul', 'Vermelho',
            'Rosa', 'Verde', 'Cinza', 'Roxo', 'Amarelo', 'Laranja'
        ]

        # Capacidades de armazenamento comuns (em GB)
        storage_options = [16, 32, 64, 128, 256, 512, 1024]

        # Tipos de senha
        password_types = ['pin', 'password', 'pattern', 'bio', 'none']

        created_devices = 0
        processed_cases = 0

        self.stdout.write(f'\nGerando dispositivos para {total_cases} cases...\n')

        for case in cases_without_devices:
            try:
                device_amount = case.requested_device_amount or 1
                devices_created_for_case = 0

                for i in range(device_amount):
                    # Seleciona categoria e modelo aleatórios
                    device_category = random.choice(device_categories)
                    
                    # Filtra modelos que pertencem à categoria (se houver relação)
                    # Como não há relação direta, vamos usar qualquer modelo
                    device_model = random.choice(device_models)
                    
                    # Gera cor aleatória (70% de chance de ter cor)
                    color = random.choice(colors) if random.random() > 0.3 else None
                    
                    # Gera IMEI (80% de chance de ter IMEI conhecido)
                    is_imei_unknown = random.random() < 0.2
                    imei_01 = None
                    imei_02 = None
                    
                    if not is_imei_unknown:
                        # Gera IMEI válido (15 dígitos)
                        imei_01 = ''.join([str(random.randint(0, 9)) for _ in range(15)])
                        # 30% de chance de ter segundo IMEI
                        if random.random() < 0.3:
                            imei_02 = ''.join([str(random.randint(0, 9)) for _ in range(15)])
                    
                    # Gera nome do proprietário (60% de chance)
                    owner_name = fake.name() if random.random() > 0.4 else None
                    
                    # Gera armazenamento interno (70% de chance)
                    internal_storage = random.choice(storage_options) if random.random() > 0.3 else None
                    
                    # Status do dispositivo
                    is_turned_on = random.choice([True, False, None])
                    is_locked = random.choice([True, False, None]) if is_turned_on else None
                    
                    # Informações de senha (apenas se estiver bloqueado)
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
                    
                    # Condição física (50% de chance de estar danificado)
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
                    if color is not None:
                        device_data['color'] = color
                    if is_imei_unknown is not None:
                        device_data['is_imei_unknown'] = is_imei_unknown
                    if imei_01 is not None:
                        device_data['imei_01'] = imei_01
                    if imei_02 is not None:
                        device_data['imei_02'] = imei_02
                    if owner_name is not None:
                        device_data['owner_name'] = owner_name
                    if internal_storage is not None:
                        device_data['internal_storage'] = internal_storage
                    if is_turned_on is not None:
                        device_data['is_turned_on'] = is_turned_on
                    if is_locked is not None:
                        device_data['is_locked'] = is_locked
                    if is_password_known is not None:
                        device_data['is_password_known'] = is_password_known
                    if password_type is not None:
                        device_data['password_type'] = password_type
                    if password is not None:
                        device_data['password'] = password
                    if is_damaged is not None:
                        device_data['is_damaged'] = is_damaged
                    if damage_description is not None:
                        device_data['damage_description'] = damage_description
                    if has_fluids is not None:
                        device_data['has_fluids'] = has_fluids
                    if fluids_description is not None:
                        device_data['fluids_description'] = fluids_description
                    if has_sim_card is not None:
                        device_data['has_sim_card'] = has_sim_card
                    if sim_card_info is not None:
                        device_data['sim_card_info'] = sim_card_info
                    if has_memory_card is not None:
                        device_data['has_memory_card'] = has_memory_card
                    if memory_card_info is not None:
                        device_data['memory_card_info'] = memory_card_info
                    if has_other_accessories is not None:
                        device_data['has_other_accessories'] = has_other_accessories
                    if other_accessories_info is not None:
                        device_data['other_accessories_info'] = other_accessories_info
                    if is_sealed is not None:
                        device_data['is_sealed'] = is_sealed
                    if security_seal is not None:
                        device_data['security_seal'] = security_seal
                    if additional_info is not None:
                        device_data['additional_info'] = additional_info
                    
                    # Usa o service para criar o dispositivo
                    device_service = CaseDeviceService(user=user)
                    case_device = device_service.create(device_data)
                    
                    devices_created_for_case += 1
                    created_devices += 1

                processed_cases += 1
                
                if processed_cases % 10 == 0:
                    self.stdout.write(f'  {processed_cases}/{total_cases} cases processados...')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erro ao criar dispositivos para case #{case.pk}: {str(e)}')
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ {created_devices} dispositivos criados para {processed_cases} cases!'
            )
        )
        
        if processed_cases < total_cases:
            self.stdout.write(
                self.style.WARNING(
                    f'Aviso: {total_cases - processed_cases} cases falharam ao processar.'
                )
            )

