# Relatório de Conformidade com o Guia de Refatoração

## Status Geral

**Data da Análise:** 2025-01-XX  
**Conformidade Geral:** ⚠️ **30%** - Apenas infraestrutura base implementada

---

## Resumo Executivo

A infraestrutura base (BaseService, BaseListView, BaseDetailView) está implementada no app `core`, mas **nenhum app está usando essa arquitetura**. Todos os apps ainda seguem o padrão antigo com lógica de negócio nas views.

---

## Análise por App

### ✅ **core** - Conformidade: 100%

**Status:** Infraestrutura completa implementada

**Componentes Implementados:**
- ✅ `BaseService` em `apps/core/services/base.py`
- ✅ `BaseListView`, `BaseDetailView`, `BaseCreateView`, `BaseUpdateView`, `BaseDeleteView` em `apps/core/mixins/views.py`
- ✅ `BaseAPIViewSet` em `apps/api/base_views.py`
- ✅ `CaseService` em `apps/core/services/case_services.py` (exemplo)
- ✅ Managers customizados em `apps/core/managers.py`
- ✅ Exemplos de refatoração em `apps/core/examples/refactored_views.py`

**Observações:**
- Infraestrutura pronta para uso
- Exemplos disponíveis para referência

---

### ❌ **cases** - Conformidade: 20%

**Status:** Service criado mas não utilizado nas views

**Problemas Identificados:**
- ❌ Views não usam `BaseListView` ou `BaseDetailView`
- ❌ `CaseListView` tem 100+ linhas com lógica de filtros nas views
- ❌ `CaseDetailView` não usa service
- ❌ `CaseCreateView`, `CaseUpdateView` não usam `BaseCreateView`/`BaseUpdateView`
- ✅ `CaseService` existe mas não é usado pelas views

**Código Atual:**
```python
# ❌ ANTES (apps/cases/views.py)
class CaseListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        # 70+ linhas de lógica de filtros
        queryset = Case.objects.filter(...)
        form = CaseSearchForm(...)
        if form.is_valid():
            # 30+ linhas de filtros manuais
        return queryset
```

**Código Esperado:**
```python
# ✅ DEPOIS
class CaseListView(BaseListView):
    model = Case
    service_class = CaseService
    search_form_class = CaseSearchForm
    template_name = 'cases/case_list.html'
```

**Ações Necessárias:**
1. Refatorar `CaseListView` para usar `BaseListView`
2. Mover lógica de filtros para `CaseService.apply_filters()`
3. Refatorar outras views para usar base classes

---

### ❌ **requisitions** - Conformidade: 10%

**Status:** Tem `services.py` mas não segue padrão BaseService

**Problemas Identificados:**
- ❌ Views não usam `BaseListView` ou `BaseDetailView`
- ❌ `ExtractionRequestListView` tem 50+ linhas com lógica nas views
- ❌ `services.py` contém funções, não classes BaseService
- ❌ Não há `ExtractionRequestService` herdando de `BaseService`
- ❌ Lógica de negócio espalhada nas views

**Código Atual:**
```python
# ❌ ANTES (apps/requisitions/services.py)
def get_distribution_summary():
    # Função standalone, não classe service
    ...

# ❌ ANTES (apps/requisitions/views/extraction_request_views.py)
class ExtractionRequestListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        # 50+ linhas de lógica
        ...
```

**Código Esperado:**
```python
# ✅ DEPOIS
class ExtractionRequestService(BaseService):
    model_class = ExtractionRequest
    
    def apply_filters(self, queryset, filters):
        # Lógica de filtros aqui
        ...

class ExtractionRequestListView(BaseListView):
    model = ExtractionRequest
    service_class = ExtractionRequestService
    search_form_class = ExtractionRequestSearchForm
```

**Ações Necessárias:**
1. Criar `ExtractionRequestService(BaseService)`
2. Migrar funções de `services.py` para métodos do service
3. Refatorar views para usar `BaseListView`/`BaseDetailView`

---

### ❌ **extractions** - Conformidade: 0%

**Status:** Nenhuma refatoração aplicada

**Problemas Identificados:**
- ❌ Views não usam `BaseListView` ou `BaseDetailView`
- ❌ `ExtractionListView` tem 100+ linhas com lógica nas views
- ❌ `MyExtractionsView` duplica lógica de `ExtractionListView`
- ❌ Não existe `ExtractionService`
- ❌ Lógica de negócio completamente nas views

**Código Atual:**
```python
# ❌ ANTES
class ExtractionListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        # 90+ linhas de lógica de filtros
        queryset = Extraction.objects.filter(...)
        form = ExtractionSearchForm(...)
        if form.is_valid():
            # 50+ linhas de filtros manuais
        return queryset
```

**Ações Necessárias:**
1. Criar `ExtractionService(BaseService)`
2. Mover lógica de filtros para service
3. Refatorar `ExtractionListView` e `MyExtractionsView` para usar `BaseListView`
4. Criar métodos específicos no service para "minhas extrações"

---

### ❌ **base_tables** - Conformidade: 0%

**Status:** Nenhuma refatoração aplicada

**Problemas Identificados:**
- ❌ Views são funções, não classes (padrão antigo)
- ❌ Não usa `BaseListView` ou `BaseDetailView`
- ❌ Não existe service para nenhum modelo
- ❌ Lógica de negócio nas views
- ❌ Código repetitivo em todas as views (organization, agency, department, etc.)

**Código Atual:**
```python
# ❌ ANTES
@login_required
@user_passes_test(is_staff_user)
def organization_list(request):
    organizations = Organization.objects.filter(...)
    return render(request, 'base_tables/organization_list.html', {...})
```

**Ações Necessárias:**
1. Criar services para cada modelo (OrganizationService, AgencyService, etc.)
2. Converter views de funções para classes usando `BaseListView`
3. Criar base service genérico para tabelas de apoio

---

### ❌ **users** - Conformidade: 0%

**Status:** Nenhuma refatoração aplicada

**Problemas Identificados:**
- ❌ Views são funções, não classes
- ❌ Não usa `BaseListView` ou `BaseDetailView`
- ❌ Não existe `UserProfileService`
- ❌ Lógica simples mas não centralizada

**Observações:**
- App simples, mas deveria seguir padrão para consistência

**Ações Necessárias:**
1. Criar `UserProfileService(BaseService)`
2. Converter views para classes (se necessário)
3. Centralizar lógica de perfil

---

## Métricas de Conformidade

| App | Views Refatoradas | Services Criados | Managers Customizados | Conformidade |
|-----|------------------|------------------|----------------------|--------------|
| **core** | ✅ N/A (infra) | ✅ Sim | ✅ Sim | **100%** |
| **cases** | ❌ 0/5 | ✅ Sim (não usado) | ❌ Não | **20%** |
| **requisitions** | ❌ 0/6 | ⚠️ Parcial | ❌ Não | **10%** |
| **extractions** | ❌ 0/3 | ❌ Não | ❌ Não | **0%** |
| **base_tables** | ❌ 0/27 | ❌ Não | ❌ Não | **0%** |
| **users** | ❌ 0/5 | ❌ Não | ❌ Não | **0%** |

---

## Padrões Violados

### 1. Lógica de Negócio nas Views ❌
**Problema:** Views contêm 50-100+ linhas de lógica de filtros e validações

**Exemplo:**
```python
# ❌ Violação
class CaseListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        queryset = Case.objects.filter(...)
        form = CaseSearchForm(...)
        if form.is_valid():
            # 30+ linhas de lógica de filtros
            if search:
                queryset = queryset.filter(Q(...) | Q(...))
            if status:
                queryset = queryset.filter(status=status)
            # ... mais 20 linhas
        return queryset
```

**Solução:**
```python
# ✅ Conforme
class CaseService(BaseService):
    def apply_filters(self, queryset, filters):
        # Lógica aqui
        ...

class CaseListView(BaseListView):
    model = Case
    service_class = CaseService
```

### 2. Consultas Não Otimizadas ❌
**Problema:** Queries sem `select_related()`/`prefetch_related()` em vários lugares

**Solução:** Usar managers customizados com queries otimizadas

### 3. Código Duplicado ❌
**Problema:** Mesma lógica repetida em múltiplas views

**Exemplo:** `ExtractionListView` e `MyExtractionsView` têm código quase idêntico

**Solução:** Usar `BaseListView` com filtros no service

### 4. Views como Funções ❌
**Problema:** `base_tables` e `users` usam funções em vez de classes

**Solução:** Converter para classes usando base views

---

## Roadmap de Refatoração

### Fase 1: Cases (Prioridade Alta) - 1-2 semanas
1. ✅ `CaseService` já existe
2. Refatorar `CaseListView` para usar `BaseListView`
3. Mover filtros para `CaseService.apply_filters()`
4. Refatorar outras views (Detail, Create, Update, Delete)
5. Testes unitários

### Fase 2: Requisitions (Prioridade Alta) - 1-2 semanas
1. Criar `ExtractionRequestService(BaseService)`
2. Migrar funções de `services.py` para métodos do service
3. Refatorar views para usar base classes
4. Testes unitários

### Fase 3: Extractions (Prioridade Média) - 1 semana
1. Criar `ExtractionService(BaseService)`
2. Refatorar `ExtractionListView` e `MyExtractionsView`
3. Mover lógica de workflow para service
4. Testes unitários

### Fase 4: Base Tables (Prioridade Baixa) - 1 semana
1. Criar services genéricos ou específicos
2. Converter views de funções para classes
3. Usar `BaseListView`/`BaseDetailView`
4. Testes unitários

### Fase 5: Users (Prioridade Baixa) - 2-3 dias
1. Criar `UserProfileService`
2. Refatorar views se necessário
3. Testes unitários

---

## Benefícios Esperados Após Refatoração

### Redução de Código
- **Antes:** ~2000 linhas de código duplicado em views
- **Depois:** ~500 linhas em services reutilizáveis
- **Redução:** ~75%

### Manutenibilidade
- Lógica centralizada em services
- Fácil adicionar APIs REST
- Testes unitários mais simples

### Performance
- Queries otimizadas em managers
- Cache estratégico em services
- Menos queries N+1

---

## Conclusão

A infraestrutura está pronta, mas **nenhum app está usando**. É necessário:

1. **Refatorar gradualmente** começando por `cases` e `requisitions`
2. **Migrar lógica** das views para services
3. **Usar base classes** em todas as views
4. **Criar managers** customizados para queries otimizadas
5. **Testar extensivamente** cada refatoração

**Estimativa Total:** 4-6 semanas para refatoração completa de todos os apps.

