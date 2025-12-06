# Análise: Commands e Uso de Services

## Resumo
Verificação de todos os management commands para identificar se estão utilizando services ou fazendo lógica diretamente nos models.

## Commands Encontrados

### 1. `load_initial_data.py` ❌
**Status:** Não usa services
**Localização:** `apps/core/management/commands/load_initial_data.py`
**Observações:**
- Faz operações diretamente nos models
- Carrega dados iniciais de JSON
- Pode criar um service específico para carregamento de dados iniciais, mas não é crítico

### 2. `export_initial_data.py` ❌
**Status:** Não usa services
**Localização:** `apps/core/management/commands/export_initial_data.py`
**Observações:**
- Faz serialização diretamente
- Exporta dados para JSON
- Não há service equivalente, mas não é crítico

### 3. `generate_test_requests.py` ❌
**Status:** Não usa services
**Localização:** `apps/core/management/commands/generate_test_requests.py`
**Observações:**
- Cria `ExtractionRequest` diretamente com `ExtractionRequest.objects.create()`
- **DEVE SER REFATORADO** para usar `ExtractionRequestService`

### 4. `create_cases_from_requests.py` ✅
**Status:** Usa services
**Localização:** `apps/core/management/commands/create_cases_from_requests.py`
**Observações:**
- Tem função `parse_request_procedures()` que duplica lógica do `ExtractionRequestService._parse_request_procedures()`
- Cria `Case` diretamente
- **DEVE SER REFATORADO** para usar `ExtractionRequestService.create_case_from_request()`

### 5. `generate_case_devices.py` ✅
**Status:** Usa services
**Localização:** `apps/core/management/commands/generate_case_devices.py`
**Observações:**
- Cria `CaseDevice` diretamente com `CaseDevice.objects.create()`
- **DEVE SER REFATORADO** para usar `CaseDeviceService`

## Services Disponíveis

### `ExtractionRequestService`
- ✅ `create_case_from_request(request_pk)` - Cria case a partir de request
- ✅ `_parse_request_procedures()` - Parse de procedimentos
- ❌ Não tem método para criar request (pode ser adicionado)

### `CaseDeviceService`
- ✅ `create()` - Cria device com validações
- ✅ `validate_business_rules()` - Valida regras de negócio

### `CaseService`
- ✅ `create()` - Cria case com validações
- ✅ `complete_registration()` - Finaliza cadastro

## Ações Recomendadas

1. **Alta Prioridade:**
   - ✅ **CONCLUÍDO:** Refatorar `create_cases_from_requests.py` para usar `ExtractionRequestService.create_case_from_request()`
   - ✅ **CONCLUÍDO:** Refatorar `generate_case_devices.py` para usar `CaseDeviceService.create()`

2. **Média Prioridade:**
   - ⏳ **PENDENTE:** Refatorar `generate_test_requests.py` para usar `ExtractionRequestService` (criar método se necessário)

3. **Baixa Prioridade:**
   - `load_initial_data.py` e `export_initial_data.py` podem continuar como estão (são utilitários de setup)

## Mudanças Realizadas

### ✅ `create_cases_from_requests.py`
- **Movido para:** `apps/core/management/commands/`
- Removida função duplicada `parse_request_procedures()`
- Agora usa `ExtractionRequestService.create_case_from_request()` que já faz:
  - Criação do Case
  - Parse de procedimentos
  - Atualização do ExtractionRequest
- Código mais limpo e reutiliza lógica existente
- Corrigido bug: criação de devices agora funciona corretamente

### ✅ `generate_case_devices.py`
- **Movido para:** `apps/core/management/commands/`
- Removido uso direto de `CaseDevice.objects.create()`
- Agora usa `CaseDeviceService.create()` que:
  - Aplica validações de negócio
  - Gerencia `created_by` automaticamente
  - Mantém consistência com o resto da aplicação

### ✅ `generate_test_requests.py`
- **Já estava em:** `apps/core/management/commands/`
- Refatorado para usar `ExtractionRequestService.create()`
- Agora aplica validações de negócio automaticamente

## Reorganização de Commands

Todos os management commands foram centralizados em `apps/core/management/commands/`:

1. `load_initial_data.py` - Carrega dados iniciais
2. `export_initial_data.py` - Exporta dados iniciais
3. `generate_test_requests.py` - Gera solicitações de teste
4. `create_cases_from_requests.py` - Cria cases a partir de requests (movido de cases)
5. `generate_case_devices.py` - Gera dispositivos para cases (movido de cases)

