# Documentação dos Management Commands

Este documento descreve todos os management commands disponíveis no sistema, suas funcionalidades, opções e exemplos de uso.

## Índice

1. [load_initial_data](#load_initial_data)
2. [export_initial_data](#export_initial_data)
3. [generate_test_requests](#generate_test_requests)
4. [create_cases_from_requests](#create_cases_from_requests)
5. [generate_case_devices](#generate_case_devices)
6. [complete_incomplete_cases](#complete_incomplete_cases)

---

## load_initial_data

**Localização:** `apps/core/management/commands/load_initial_data.py`

### Descrição

Carrega dados iniciais do sistema a partir de arquivos JSON localizados na pasta `initial_data/`. Este command é essencial para inicializar o banco de dados com dados de referência como organizações, agências, unidades, usuários, categorias, etc.

### Arquivos Suportados

O command carrega os seguintes arquivos na ordem especificada:

1. `01_employee_positions.json` - Cargos de funcionários
2. `02_organizations.json` - Organizações, agências e unidades
3. `03_pcce_agency_units.json` - Departamentos e unidades da PCCE
4. `04_users.json` - Usuários do sistema
5. `05_extraction_agency.json` - Agência de extração e unidades
6. `06_crime_category.json` - Categorias de crime
7. `07_device_category.json` - Categorias de dispositivos
8. `08_device_brands_models.json` - Marcas e modelos de dispositivos
9. `09_procedure_category.json` - Categorias de procedimento
10. `10_extraction_agency_and_settings.json` - Configurações da agência de extração
11. `11_storage_media.json` - Mídias de armazenamento
12. `12_evidence_storage_locations.json` - Locais de armazenamento de evidências

### Opções

- `--file <nome_arquivo>`: Carrega apenas um arquivo específico (sem caminho)
- `--clear`: Limpa todos os dados existentes antes de carregar (cuidado em produção!)

### Exemplos de Uso

```bash
# Carrega todos os arquivos na ordem correta
python manage.py load_initial_data

# Carrega apenas um arquivo específico
python manage.py load_initial_data --file 11_storage_media.json

# Limpa dados existentes e carrega tudo novamente
python manage.py load_initial_data --clear

# Carrega apenas usuários
python manage.py load_initial_data --file 04_users.json
```

### Observações

- O command usa transações para garantir consistência dos dados
- Dados duplicados são ignorados (usa `get_or_create`)
- A ordem de carregamento é importante devido às dependências entre modelos
- O uso de `--clear` em produção pode ser perigoso

---

## export_initial_data

**Localização:** `apps/core/management/commands/export_initial_data.py`

### Descrição

Exporta dados de `ExtractionAgency` e `Settings` (GeneralSettings, EmailSettings, ReportsSettings) para um arquivo JSON na pasta `initial_data/`. Útil para backup ou migração de configurações.

### Opções

- `--output <nome_arquivo>`: Nome do arquivo de saída (padrão: `extraction_agency_and_settings.json`)

### Exemplos de Uso

```bash
# Exporta para o arquivo padrão
python manage.py export_initial_data

# Exporta para um arquivo específico
python manage.py export_initial_data --output minha_exportacao.json
```

### Formato de Saída

O arquivo gerado contém:
- `extraction_agency`: Dados da agência de extração (incluindo logo em base64)
- `settings.general`: Configurações gerais do sistema
- `settings.email`: Configurações de email
- `settings.reports`: Configurações de relatórios (incluindo logos em base64)

### Observações

- Logos são convertidos para base64 no JSON
- O diretório `initial_data/` é criado automaticamente se não existir
- O arquivo é sobrescrito se já existir

---

## generate_test_requests

**Localização:** `apps/core/management/commands/generate_test_requests.py`

### Descrição

Gera solicitações de extração (`ExtractionRequest`) para testes usando dados aleatórios com Faker. Útil para popular o banco de dados com dados de teste realistas.

### Opções

- `username` (obrigatório): Login do usuário que criará as solicitações
- `quantity` (obrigatório): Quantidade de solicitações a serem geradas
- `--max-devices <número>`: Quantidade máxima de dispositivos por solicitação (padrão: 1)

### Exemplos de Uso

```bash
# Gera 50 solicitações de teste
python manage.py generate_test_requests admin 50

# Gera 100 solicitações com até 3 dispositivos cada
python manage.py generate_test_requests admin 100 --max-devices 3

# Gera 10 solicitações com 1 dispositivo cada (padrão)
python manage.py generate_test_requests admin 10
```

### Dados Gerados

- **Solicitações**: Distribuídas aleatoriamente entre unidades de extração e agências
- **Procedimentos**: 1 a 5 procedimentos por solicitação (formato: "IP 1234/2024, PJ 5678/2024")
- **Dispositivos**: Quantidade aleatória entre 1 e `max-devices`
- **Datas**: Solicitações com datas aleatórias (entre hoje e 4 anos atrás)
- **Informações adicionais**: 50% de chance de ter informações adicionais

### Observações

- Usa `ExtractionRequestService` para criar as solicitações (aplica validações)
- Requer que existam: unidades de agência, unidades de extração, cargos, categorias de crime
- Categorias de procedimento são opcionais (usa valores padrão se não houver)

---

## create_cases_from_requests

**Localização:** `apps/core/management/commands/create_cases_from_requests.py`

### Descrição

Cria `Case` a partir de `ExtractionRequest` que ainda não possuem case vinculado. Este command processa solicitações de extração e cria os processos correspondentes, parseando procedimentos e atualizando o status das solicitações.

### Opções

- `--username <login>`: Login do usuário que criará os cases (obrigatório se não fornecido, solicita interativamente)
- `--limit <número>`: Quantidade de extraction_requests a processar (opcional, processa todas se não informado)
- `--dry-run`: Apenas mostra quais extraction_requests seriam processados sem criar os cases
- `--create-devices`: Cria `case_devices` automaticamente baseado no `requested_device_amount`

### Exemplos de Uso

```bash
# Processa todas as solicitações sem case
python manage.py create_cases_from_requests --username admin

# Processa apenas 10 solicitações
python manage.py create_cases_from_requests --username admin --limit 10

# Ver o que seria processado sem fazer alterações
python manage.py create_cases_from_requests --username admin --dry-run

# Cria cases e devices automaticamente
python manage.py create_cases_from_requests --username admin --create-devices
```

### Funcionalidades

1. **Busca solicitações**: Encontra todas as `ExtractionRequest` sem case vinculado
2. **Cria cases**: Usa `ExtractionRequestService.create_case_from_request()` para criar
3. **Parse de procedimentos**: Tenta parsear `request_procedures` e criar `CaseProcedure`
4. **Atualiza solicitação**: Marca a solicitação como recebida e atualiza status
5. **Cria devices** (opcional): Se `--create-devices`, cria devices básicos aleatórios

### Observações

- Usa `ExtractionRequestService` que já faz parse de procedimentos automaticamente
- Falhas no parse de procedimentos não impedem a criação do case
- A criação de devices requer categorias e modelos cadastrados
- O command é interativo se `--username` não for fornecido

---

## generate_case_devices

**Localização:** `apps/core/management/commands/generate_case_devices.py`

### Descrição

Gera dispositivos aleatórios (`CaseDevice`) para cases que não possuem dispositivos cadastrados. Usa Faker para gerar dados realistas de teste.

### Opções

- `--username <login>`: Login do usuário que criará os dispositivos (opcional, usa o primeiro usuário se não informado)
- `--dry-run`: Apenas mostra quais cases seriam processados sem criar os dispositivos

### Exemplos de Uso

```bash
# Gera dispositivos para todos os cases sem devices
python manage.py generate_case_devices

# Especifica o usuário
python manage.py generate_case_devices --username admin

# Ver o que seria processado
python manage.py generate_case_devices --dry-run
```

### Dados Gerados

Cada device gerado inclui:

- **Básicos**: Categoria, modelo, cor
- **IMEI**: 80% de chance de ter IMEI conhecido (15 dígitos)
- **Proprietário**: 60% de chance de ter nome do proprietário
- **Armazenamento**: 70% de chance de ter capacidade especificada
- **Status**: Ligado/desligado, bloqueado/desbloqueado
- **Senha**: Se bloqueado, 50% de chance de senha conhecida (PIN, padrão, biometria, etc.)
- **Condição física**: 50% de chance de estar danificado
- **Fluidos**: 10% de chance de ter fluidos
- **Acessórios**: SIM card, cartão de memória, outros acessórios
- **Lacre**: 40% de chance de ter lacre de segurança
- **Informações adicionais**: 30% de chance de ter observações

### Observações

- Usa `CaseDeviceService` para criar os devices (aplica validações)
- Requer categorias e modelos de dispositivo cadastrados
- Cria a quantidade de devices especificada em `requested_device_amount` de cada case
- Apenas processa cases que têm `requested_device_amount > 0`

---

## complete_incomplete_cases

**Localização:** `apps/core/management/commands/complete_incomplete_cases.py`

### Descrição

Completa cases com cadastro incompleto, preenchendo dados faltantes (devices e procedures) e finalizando o cadastro automaticamente. Ideal para gerar dados de teste completos.

### Opções

- `--username <login>`: Login do usuário que processará os cases (opcional, usa o primeiro usuário se não informado)
- `--limit <número>`: Quantidade máxima de cases a processar (opcional, processa todos se não informado)
- `--dry-run`: Apenas mostra quais cases seriam processados sem fazer alterações
- `--skip-devices`: Não cria devices se não existirem (apenas completa dados existentes)
- `--skip-procedures`: Não cria procedures se não existirem (apenas completa dados existentes)

### Exemplos de Uso

```bash
# Completa todos os cases incompletos
python manage.py complete_incomplete_cases

# Processa apenas 20 cases
python manage.py complete_incomplete_cases --limit 20

# Ver o que seria processado
python manage.py complete_incomplete_cases --dry-run

# Especifica usuário
python manage.py complete_incomplete_cases --username admin

# Não cria devices, apenas procedures
python manage.py complete_incomplete_cases --skip-devices
```

### Funcionalidades

1. **Busca cases incompletos**: Filtra cases onde `registration_completed_at` é `None`
2. **Cria devices faltantes**: Se não houver devices, cria usando dados aleatórios realistas
3. **Cria procedures faltantes**: 
   - Tenta parsear `request_procedures` primeiro
   - Se não conseguir, cria um procedure genérico
4. **Finaliza cadastro**: Usa `CaseService.complete_registration()` para finalizar
   - Gera número do case automaticamente
   - Atualiza status para `WAITING_EXTRACTOR`
   - Adiciona nota de finalização automática

### Dados Gerados

- **Devices**: Mesmos dados detalhados do `generate_case_devices`
- **Procedures**: Parse de `request_procedures` ou criação de procedure genérico
- **Finalização**: Usa service para garantir todas as validações

### Observações

- Usa `CaseService` e `CaseDeviceService` para garantir validações
- Requer categorias e modelos de dispositivo se for criar devices
- Requer categorias de procedimento se for criar procedures
- O command é robusto e continua processando mesmo se alguns cases falharem
- Mostra estatísticas detalhadas ao final

---

## Ordem Recomendada de Execução

Para popular o banco de dados com dados de teste completos, siga esta ordem:

```bash
# 1. Carregar dados iniciais (organizações, usuários, categorias, etc.)
python manage.py load_initial_data

# 2. Gerar solicitações de extração de teste
python manage.py generate_test_requests admin 100 --max-devices 3

# 3. Criar cases a partir das solicitações
python manage.py create_cases_from_requests --username admin

# 4. Gerar devices para cases que não têm
python manage.py generate_case_devices --username admin

# 5. Completar cases incompletos (cria o que falta e finaliza)
python manage.py complete_incomplete_cases --username admin
```

---

## Troubleshooting

### Erro: "Não há unidades de agência cadastradas"

**Solução**: Execute `python manage.py load_initial_data` primeiro para carregar dados iniciais.

### Erro: "Usuário não encontrado"

**Solução**: Verifique se o usuário existe ou crie um com `python manage.py createsuperuser`.

### Erro: "Não há categorias de dispositivo cadastradas"

**Solução**: Execute `python manage.py load_initial_data --file 07_device_category.json`.

### Cases não são finalizados

**Verifique**:
- Se há pelo menos 1 device cadastrado
- Se há pelo menos 1 procedure cadastrado
- Se o case tem `extraction_unit` definido (necessário para gerar número)

### Performance

Para grandes volumes de dados:
- Use `--limit` para processar em lotes
- Execute commands em horários de menor uso
- Monitore o uso de memória e CPU

---

## Notas Técnicas

- Todos os commands usam **services** para garantir validações e regras de negócio
- Commands que criam dados usam **transações** para garantir consistência
- Dados são criados com **soft delete** (campo `deleted_at`)
- Todos os registros incluem **auditoria** (`created_by`, `updated_by`, `version`)
- Commands são **idempotentes** quando possível (não duplicam dados)

---

## Contribuindo

Ao criar novos commands:

1. Coloque em `apps/core/management/commands/`
2. Use services quando possível
3. Adicione opções `--dry-run` para commands destrutivos
4. Documente neste arquivo
5. Use transações para operações críticas
6. Trate erros graciosamente e forneça feedback útil

