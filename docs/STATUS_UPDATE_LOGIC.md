# Lógica de Atualização de Status do Case

Este documento descreve como o status do `Case` é atualizado automaticamente com base no status das extrações associadas.

## Método Implementado

O método `update_status_based_on_extractions()` foi adicionado ao modelo `Case` e é chamado automaticamente sempre que o status de uma extração é modificado.

## Regras de Negócio

O status do Case é determinado pela análise dos status de todas as extrações não deletadas associadas ao case:

### 1. **COMPLETED** (Concluído)
- **Quando**: Todas as extrações estão com status `completed`
- **Exemplo**: Case com 3 extrações, todas finalizadas

### 2. **IN_PROGRESS** (Em Progresso)
- **Quando**: Pelo menos uma extração está com status `in_progress`
- **Prioridade**: Alta - mesmo que existam outras pausadas ou completas
- **Exemplo**: Case com 5 extrações, 2 em progresso, 2 completas, 1 pausada

### 3. **PAUSED** (Pausado)
- **Quando**: 
  - Todas as extrações estão pausadas, OU
  - Mix apenas de pausadas e completas (mas pelo menos uma pausada)
- **Exemplo**: Case com 3 extrações, todas pausadas

### 4. **WAITING_START** (Aguardando Início)
- **Quando**: Pelo menos uma extração está `assigned` (atribuída a um extrator)
- **Exemplo**: Case com 2 extrações atribuídas aguardando início

### 5. **WAITING_EXTRACTOR** (Aguardando Extrator)
- **Quando**: Todas as extrações estão `pending` (sem atribuição)
- **Exemplo**: Case recém criado com extrações aguardando extrator

### 6. **DRAFT** (Cadastro Incompleto)
- **Quando**: Case não possui extrações
- **Nota**: Mantém status atual se já for `WAITING_COLLECT`

## Pontos de Atualização

O método `update_status_based_on_extractions()` é chamado automaticamente nos seguintes pontos:

### Views de Extração (`apps/extractions/views.py`)
1. **ExtractionAssignToMeView** - Ao atribuir extração ao extrator
2. **ExtractionUnassignFromMeView** - Ao remover atribuição
3. **ExtractionStartView** - Ao iniciar extração
4. **ExtractionPauseView** - Ao pausar extração
5. **ExtractionResumeView** - Ao retomar extração
6. **ExtractionFinishView** - Ao finalizar extração

### Views de Case (`apps/cases/views.py`)
7. **CreateExtractionsView** - Ao criar extrações automaticamente para dispositivos

### Métodos do Modelo Extraction (`apps/cases/models.py`)
8. **assign_extraction()** - Método de modelo para atribuição
9. **start_extraction()** - Método de modelo para iniciar
10. **pause_extraction()** - Método de modelo para pausar
11. **complete_extraction()** - Método de modelo para completar

## Fluxo de Status do Case

```
DRAFT
  ↓ (criar extrações)
WAITING_EXTRACTOR (todas pending)
  ↓ (atribuir extrator)
WAITING_START (pelo menos uma assigned)
  ↓ (iniciar extração)
IN_PROGRESS (pelo menos uma in_progress)
  ↓ (pausar todas)
PAUSED (todas paused)
  ↓ (retomar)
IN_PROGRESS
  ↓ (finalizar todas)
COMPLETED
```

## Exemplos Práticos

### Exemplo 1: Case com 3 extrações
- Extração 1: `pending`
- Extração 2: `pending`
- Extração 3: `pending`
- **Status do Case**: `WAITING_EXTRACTOR`

### Exemplo 2: Após atribuir extratores
- Extração 1: `assigned`
- Extração 2: `assigned`
- Extração 3: `pending`
- **Status do Case**: `WAITING_START`

### Exemplo 3: Iniciando trabalho
- Extração 1: `in_progress`
- Extração 2: `assigned`
- Extração 3: `pending`
- **Status do Case**: `IN_PROGRESS`

### Exemplo 4: Progresso misto
- Extração 1: `completed`
- Extração 2: `in_progress`
- Extração 3: `paused`
- **Status do Case**: `IN_PROGRESS` (prioridade para in_progress)

### Exemplo 5: Todas pausadas
- Extração 1: `paused`
- Extração 2: `paused`
- Extração 3: `paused`
- **Status do Case**: `PAUSED`

### Exemplo 6: Trabalho concluído
- Extração 1: `completed`
- Extração 2: `completed`
- Extração 3: `completed`
- **Status do Case**: `COMPLETED`

## Considerações Técnicas

- O método utiliza `values_list` para performance, buscando apenas os status das extrações
- Apenas extrações não deletadas são consideradas (`deleted_at__isnull=True`)
- A atualização é feita apenas se houver mudança de status (`if self.status != new_status`)
- Utiliza `update_fields=['status']` para atualizar apenas o campo necessário

## Testando

Para testar o comportamento:

1. Crie um Case com dispositivos
2. Crie extrações para os dispositivos
3. Modifique o status das extrações através das views
4. Observe o status do Case sendo atualizado automaticamente

```python
# Exemplo de teste manual no Django shell
from apps.cases.models import Case

case = Case.objects.get(pk=1)
print(f"Status atual: {case.status}")

# Modifique extrações...
# O status será atualizado automaticamente

case.refresh_from_db()
print(f"Novo status: {case.status}")
```
