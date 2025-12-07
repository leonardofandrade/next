# Sistema de Filtragem por Extraction Unit

## Objetivo

Implementar controle de acesso granular para usuários extratores (`ExtractorUser`), garantindo que eles possam acessar apenas dados (extraction_requests, cases e extractions) das extraction_units às quais estão relacionados.

## Arquitetura da Solução

A solução implementa uma abordagem em **múltiplas camadas**:

### 1. Camada de View (ExtractionUnitFilterMixin)

**Localização:** `apps/core/mixins/views.py`

```python
class ExtractionUnitFilterMixin:
    """
    Mixin que filtra automaticamente queryset baseado nas 
    extraction_units do usuário extrator.
    """
    def get_queryset(self):
        # Filtragem automática no queryset da view
```

**Como funciona:**
- Intercepta o método `get_queryset()` das views
- Identifica se o usuário é um extrator
- Filtra automaticamente os dados pelas extraction_units do usuário
- Superusuários têm acesso irrestrito

**Aplicado em:**
- `CaseListView`, `CaseDetailView`, `CaseUpdateView`
- `ExtractionRequestListView`, `ExtractionRequestDetailView`, `ExtractionRequestUpdateView`
- `ExtractionRequestNotReceivedView`, `ExtractionRequestDistributionListView`
- `ExtractionListView`

### 2. Camada de Service (Métodos Privados)

**Localização:** `apps/cases/services.py`, `apps/requisitions/services.py`, `apps/extractions/services.py`

```python
def _apply_extraction_unit_filter(self, queryset: QuerySet) -> QuerySet:
    """
    Filtra queryset baseado nas extraction_units do usuário extrator.
    Superusuários veem todos os dados.
    """
```

**Como funciona:**
- Método privado chamado em `get_queryset()` de cada service
- Busca as extraction_units vinculadas ao usuário via `ExtractorUser`
- Aplica filtro SQL no queryset base
- Retorna queryset filtrado ou completo (para não-extratores)

### 3. Métodos Utilitários (BaseService)

**Localização:** `apps/core/services/base.py`

```python
def get_user_extraction_units(self) -> List[int]:
    """Retorna lista de IDs das extraction_units do usuário"""

def is_extractor_user(self) -> bool:
    """Verifica se o usuário é um extrator"""
```

**Benefícios:**
- Reutilização de lógica comum
- Facilita testes unitários
- Centraliza queries de verificação

## Fluxo de Dados

```
┌─────────────┐
│   Request   │
│   (User)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  ExtractionUnitFilterMixin  │ ◄─── Mixin em Views
│  get_queryset()             │
└──────┬──────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│     Service Layer            │
│  _apply_extraction_unit_     │ ◄─── Filtro em Services
│  filter()                    │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│   Database Query             │
│   WHERE extraction_unit_id   │ ◄─── Query SQL filtrada
│   IN (...)                   │
└──────────────────────────────┘
```

## Estrutura de Relacionamentos

```
User
 │
 ├─► ExtractorUser (1:N)
      │
      └─► ExtractionUnitExtractor (1:N)
           │
           └─► ExtractionUnit

ExtractionRequest ──┬─► extraction_unit (FK)
Case              ──┤
Extraction ────────►│ (via case_device.case.extraction_unit)
```

## Regras de Negócio

### Para Superusuários
- ✅ Acesso irrestrito a todos os dados
- ✅ Nenhum filtro aplicado

### Para Usuários Extratores
- ✅ Acesso apenas a dados de suas extraction_units
- ✅ Filtro aplicado automaticamente em views e services
- ⛔ Retorna queryset vazio se não tiver extraction_units vinculadas

### Para Outros Usuários (Staff, etc.)
- ✅ Acesso completo (sem filtro)
- ℹ️ Outras regras de permissão devem ser aplicadas conforme necessário

## Exemplos de Uso

### Em Views

```python
# Apenas adicionar o mixin
class CaseListView(ExtractionUnitFilterMixin, LoginRequiredMixin, ServiceMixin, ListView):
    # O filtro é aplicado automaticamente
    pass
```

### Em Services

```python
# O filtro já está no get_queryset()
service = CaseService(user=request.user)
cases = service.list_filtered()  # Já retorna filtrado
```

### Verificação Manual

```python
# Para casos específicos onde você precisa verificar
service = CaseService(user=request.user)

if service.is_extractor_user():
    extraction_units = service.get_user_extraction_units()
    # Lógica específica para extratores
```

## Considerações de Segurança

### ✅ Proteções Implementadas

1. **Filtragem no nível do QuerySet**: Filtros SQL não podem ser contornados
2. **Dupla camada**: View + Service garantem consistência
3. **Exceções tratadas**: Erros retornam queryset vazio (fail-safe)
4. **Superusuários sempre protegidos**: Mantêm acesso total

### 🔒 Boas Práticas

1. **Sempre use o Service Layer**: Não faça queries diretas no model
2. **Não confie apenas em templates**: Filtros de UI não são segurança
3. **Teste com diferentes perfis**: Superuser, Extractor, Staff
4. **Logs de auditoria**: Os modelos AuditedModel já registram created_by/updated_by

## Testing

### Cenários de Teste Recomendados

```python
def test_extractor_sees_only_own_units():
    # Extrator deve ver apenas suas extraction_units
    
def test_superuser_sees_all():
    # Superusuário vê tudo
    
def test_extractor_without_units():
    # Extrator sem unidades vê queryset vazio
    
def test_non_extractor_sees_all():
    # Usuário staff (não extrator) vê tudo
```

## Manutenção e Extensão

### Adicionar Filtro em Nova View

1. Importar o mixin:
```python
from apps.core.mixins.views import ExtractionUnitFilterMixin
```

2. Adicionar na hierarquia da classe (antes de LoginRequiredMixin):
```python
class MyNewView(ExtractionUnitFilterMixin, LoginRequiredMixin, ListView):
    pass
```

### Adicionar Filtro em Novo Service

1. Adicionar método privado:
```python
def _apply_extraction_unit_filter(self, queryset: QuerySet) -> QuerySet:
    # Copiar implementação dos services existentes
```

2. Chamar no `get_queryset()`:
```python
def get_queryset(self) -> QuerySet:
    queryset = super().get_queryset()
    queryset = self._apply_extraction_unit_filter(queryset)
    return queryset
```

### Adicionar Novo Campo de Filtro

Se o modelo usa campo diferente de `extraction_unit`:

```python
# No mixin ou service
if hasattr(queryset.model, 'meu_campo_extraction_unit'):
    return queryset.filter(meu_campo_extraction_unit__in=extraction_unit_ids)
```

## Troubleshooting

### Problema: Extrator não vê dados esperados
**Solução:** Verificar se o ExtractorUser está vinculado às ExtractionUnits corretas via ExtractionUnitExtractor

### Problema: Superusuário não vê todos os dados
**Solução:** Verificar se `is_superuser=True` no usuário

### Problema: Erro ao aplicar filtro
**Solução:** Verificar se o modelo tem o campo `extraction_unit` ou ajustar o caminho do filtro

### Problema: Filtro não está sendo aplicado
**Solução:** 
1. Verificar se o mixin está antes de LoginRequiredMixin na herança
2. Verificar se `super().get_queryset()` está sendo chamado
3. Verificar se o service tem `_apply_extraction_unit_filter()` implementado

## Performance

### Otimizações Implementadas

1. **Prefetch Related**: `prefetch_related('extraction_unit_extractors')`
2. **Values List**: Usa `values_list('extraction_unit_id', flat=True)` para queries eficientes
3. **Cache de Resultados**: Lista de extraction_units é montada uma vez por request

### Monitoramento

Use Django Debug Toolbar para verificar:
- Número de queries geradas
- Queries N+1 (não devem existir com os prefetch_related)
- Tempo de execução das queries

## Referências

- Django QuerySet API: https://docs.djangoproject.com/en/stable/ref/models/querysets/
- Django Mixins: https://docs.djangoproject.com/en/stable/topics/class-based-views/mixins/
- Row-Level Permissions: https://docs.djangoproject.com/en/stable/topics/auth/customizing/
