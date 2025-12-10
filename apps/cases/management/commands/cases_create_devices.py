import random
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from apps.cases.models import Case, CaseDevice, CaseProcedure
from apps.cases.services.case_device_service import CaseDeviceService
from apps.cases.services.case_procedure_service import CaseProcedureService
from apps.base_tables.models import (
    DeviceCategory, DeviceModel, ProcedureCategory
)


class Command(BaseCommand):
    help = "Busca casos sem case_devices e popula com dados randômicos"

    def add_arguments(self, parser):
        parser.add_argument(
            '--u',
            type=str,
            help='Login do usuário para registrar como created_by (obrigatório)',
            required=True
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limite de casos para processar (padrão: todos)',
            default=None
        )

    def handle(self, *args, **options):
        username = options['u']
        limit = options.get('limit')

        # Validar usuário
        try:
            created_by_user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"Usuário com login '{username}' não encontrado")

        # Buscar casos sem case_devices
        cases_without_data = self._find_cases_without_data()
        
        # Aplicar limite se especificado
        if limit:
            cases_without_data = cases_without_data[:limit]
        
        if not cases_without_data:
            self.stdout.write(
                self.style.WARNING("Nenhum caso encontrado sem case_devices.")
            )
            return

        # Buscar dados necessários
        device_categories = list(DeviceCategory.objects.filter(deleted_at__isnull=True))
        device_models = list(DeviceModel.objects.filter(deleted_at__isnull=True))
        procedure_categories = list(ProcedureCategory.objects.filter(deleted_at__isnull=True))

        if not device_categories:
            raise CommandError("Nenhum DeviceCategory encontrado no sistema")
        if not device_models:
            raise CommandError("Nenhum DeviceModel encontrado no sistema")
        if not procedure_categories:
            raise CommandError("Nenhum ProcedureCategory encontrado no sistema")

        # Dados para geração randômica
        device_data = self._get_device_data()
        document_data = self._get_document_data()

        # Processar casos
        total_devices_created = 0
        total_documents_created = 0
        
        with transaction.atomic():
            for case in cases_without_data:
                self.stdout.write(f"Processando caso: {case}")
                
                # Criar dispositivos
                devices_created = self._create_devices_for_case(
                    case, device_categories, device_models, 
                    device_data, created_by_user
                )
                total_devices_created += devices_created
                
                # Criar procedimentos (1 por caso)
                documents_created = self._create_procedures_for_case(
                    case, procedure_categories, 
                    document_data, created_by_user
                )
                total_documents_created += documents_created

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ População de dados concluída!\n"
                f"📊 Estatísticas:\n"
                f"   • Casos processados: {len(cases_without_data)}\n"
                f"   • Dispositivos criados: {total_devices_created}\n"
                f"   • Procedimentos criados: {total_documents_created}\n"
                f"   • Created by: {created_by_user.username}"
            )
        )

    def _find_cases_without_data(self):
        """Busca casos que não possuem case_devices ATIVOS (não deletados)"""
        # Casos sem devices ATIVOS
        # Usa annotate para contar apenas registros não deletados
        from django.db.models import Count
        
        cases_without_data = Case.objects.annotate(
            device_count=Count(
                'case_devices',
                filter=Q(case_devices__deleted_at__isnull=True)
            )
        ).filter(
            device_count=0
        ).distinct()
        
        return list(cases_without_data)

    def _get_device_data(self):
        """Dados para geração randômica de dispositivos"""
        return {
            'colors': [
                'Preto', 'Branco', 'Azul', 'Vermelho', 'Dourado', 'Prata',
                'Rosa', 'Verde', 'Roxo', 'Cinza', 'Amarelo', 'Laranja'
            ],
            'owner_names': [
                'João Silva', 'Maria Santos', 'Pedro Oliveira', 'Ana Costa',
                'Carlos Ferreira', 'Lucia Rodrigues', 'Roberto Alves',
                'Fernanda Lima', 'Antonio Pereira', 'Sandra Martins'
            ],
            'storage_options': [32, 64, 128, 256, 512, 1024],
            'password_types': ['pin', 'password', 'pattern', 'bio', 'none'],
            'damage_descriptions': [
                'Tela trincada', 'Arranhões na tela', 'Cantos amassados',
                'Risco no corpo', 'Botão danificado', 'Sem danos visíveis'
            ],
            'fluids_descriptions': [
                'Água', 'Sangue', 'Óleo', 'Bebida', 'Nenhum fluido detectado'
            ],
            'sim_card_info': [
                'Chip ativo', 'Chip bloqueado', 'Sem chip', 'Chip danificado'
            ],
            'memory_card_info': [
                'Cartão 32GB', 'Cartão 64GB', 'Cartão 128GB', 'Sem cartão'
            ],
            'security_seals': [
                'LACRE001', 'LACRE002', 'LACRE003', 'LACRE004', 'LACRE005'
            ]
        }

    def _get_document_data(self):
        """Dados para geração randômica de documentos"""
        return {
            'document_numbers': [
                'DOC001', 'DOC002', 'DOC003', 'DOC004', 'DOC005',
                'PROC001', 'PROC002', 'PROC003', 'PROC004', 'PROC005',
                'REL001', 'REL002', 'REL003', 'REL004', 'REL005'
            ],
            'additional_info_options': [
                'Documento de investigação', 'Relatório técnico',
                'Laudo pericial', 'Termo de apreensão', 'Auto de flagrante',
                'Mandado de busca', 'Relatório de diligência'
            ]
        }

    def _create_devices_for_case(self, case, device_categories, device_models, 
                                device_data, created_by_user):
        """Cria dispositivos randômicos para um caso baseado na quantidade solicitada"""
        devices_created = 0
        device_service = CaseDeviceService(user=created_by_user)
        
        # Usar requested_device_amount do case
        if case.requested_device_amount and case.requested_device_amount > 0:
            devices_to_create = case.requested_device_amount
            self.stdout.write(f"  📊 Quantidade solicitada: {devices_to_create} dispositivo(s)")
        else:
            # Se não tiver quantidade solicitada, não criar dispositivos
            self.stdout.write(f"  ⚠️  Caso não possui quantidade solicitada (requested_device_amount), pulando criação de dispositivos")
            return 0
        
        for i in range(devices_to_create):
            device_category = random.choice(device_categories)
            
            # Escolher um modelo aleatório (DeviceModel não tem relação direta com DeviceCategory)
            device_model = random.choice(device_models) if device_models else None
            
            # Gerar IMEI se não for desconhecido
            is_imei_unknown = random.choice([True, False])
            imei_01 = None
            if not is_imei_unknown:
                # Gerar IMEI válido (15 dígitos)
                imei_01 = self._generate_valid_imei()
            
            # Preparar dados do dispositivo
            device_color = random.choice(device_data['colors'])
            
            # Verificar se já existe dispositivo com mesmo case, model e color
            existing_device = CaseDevice.objects.filter(
                case=case,
                device_model=device_model,
                color=device_color
            ).exists()
            
            if existing_device:
                # Gerar cor única adicionando sufixo
                device_color = f"{device_color}_{random.randint(100, 999)}"
            
            device_data_dict = {
                'is_imei_unknown': is_imei_unknown,
                'imei_01': imei_01,
                'owner_name': random.choice(device_data['owner_names']),
                'internal_storage': random.choice(device_data['storage_options']),
                'is_turned_on': random.choice([True, False]),
                'is_locked': random.choice([True, False]),
                'is_password_known': random.choice([True, False]),
                'password_type': random.choice(device_data['password_types']),
                'password': f"pass{random.randint(1000, 9999)}" if random.choice([True, False]) else None,
                'is_damaged': random.choice([True, False]),
                'damage_description': random.choice(device_data['damage_descriptions']) if random.choice([True, False]) else None,
                'has_fluids': random.choice([True, False]),
                'fluids_description': random.choice(device_data['fluids_descriptions']) if random.choice([True, False]) else None,
                'has_sim_card': random.choice([True, False]),
                'sim_card_info': random.choice(device_data['sim_card_info']) if random.choice([True, False]) else None,
                'has_memory_card': random.choice([True, False]),
                'memory_card_info': random.choice(device_data['memory_card_info']) if random.choice([True, False]) else None,
                'has_other_accessories': random.choice([True, False]),
                'other_accessories_info': f"Acessórios diversos {random.randint(1, 100)}" if random.choice([True, False]) else None,
                'is_sealed': random.choice([True, False]),
                'security_seal': random.choice(device_data['security_seals']) if random.choice([True, False]) else None,
                'additional_info': f"Dispositivo {i+1} do caso {case}",
                'created_by': created_by_user,
                'updated_by': created_by_user
            }
            
            try:
                # Usar o service para criar o dispositivo
                device = device_service.create({
                    'case': case,
                    'device_category': device_category,
                    'device_model': device_model,
                    'color': device_color,
                    **device_data_dict
                })
                
                devices_created += 1
                self.stdout.write(f"  📱 Dispositivo criado: {device}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Erro ao criar dispositivo: {e}")
                )
        
        return devices_created

    def _create_procedures_for_case(self, case, procedure_categories, 
                                 document_data, created_by_user):
        """Cria um procedimento randômico para um caso"""
        procedure_service = CaseProcedureService(user=created_by_user)
        
        procedure_category = random.choice(procedure_categories)
        document_number = random.choice(document_data['document_numbers'])
        
        # Verificar se já existe procedimento com mesma categoria e número
        existing_proc = CaseProcedure.objects.filter(
            case=case,
            procedure_category=procedure_category,
            number=document_number,
            deleted_at__isnull=True
        ).exists()
        
        if existing_proc:
            # Gerar número único
            document_number = f"{document_number}_{random.randint(100, 999)}"
        
        try:
            # Usar o service para criar o procedimento
            procedure = procedure_service.create({
                'case': case,
                'number': document_number,
                'procedure_category': procedure_category,
            })
            
            self.stdout.write(f"  📄 Procedimento criado: {procedure}")
            return 1
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Erro ao criar procedimento: {e}")
            )
            return 0

    def _generate_valid_imei(self):
        """Gera um IMEI válido de 15 dígitos"""
        # Gera 14 dígitos aleatórios
        imei_base = ''.join([str(random.randint(0, 9)) for _ in range(14)])
        
        # Calcula o dígito verificador usando o algoritmo Luhn
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        # Calcula o dígito verificador
        checksum = luhn_checksum(imei_base)
        check_digit = (10 - checksum) % 10
        
        return imei_base + str(check_digit)
