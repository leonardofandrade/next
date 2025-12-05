# Guia de Refatoração: Centralizando Lógica de Negócio

## Visão Geral

Este guia apresenta uma abordagem estruturada para centralizar a lógica de negócio em seu projeto Django, preparando-o para futuras APIs REST e melhorando a manutenibilidade.

## Problemas Identificados

### Antes da Refatoração:
- ❌ Lógica de negócio espalhada nas views
- ❌ Consultas SQL duplicadas em vários lugares
- ❌ Views CRUD repetitivas (50+ linhas por view)
- ❌ Dificuldade para reutilizar código em APIs
- ❌ Testes unitários complexos

### Depois da Refatoração:
- ✅ Lógica centralizada em services
- ✅ Consultas otimizadas em managers customizados
- ✅ Views enxutas (5-10 linhas)
- ✅ Código reutilizável para APIs
- ✅ Testes focados e simples

## Arquitetura Proposta

```
┌─────────────────────────────────────────┐
│                  Views                  │
│  (Web + API) - Apenas apresentação      │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│              Services                   │
│     Lógica de negócio centralizada      │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│             Managers                    │
│      Consultas otimizadas               │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│              Models                     │
│         Estrutura de dados              │
└─────────────────────────────────────────┘
```

## Como Implementar

### 1. Atualizar Models com Managers

```python
# apps/cases/models.py
from apps.core.managers import CaseManager, ExtractionManager

class Case(AbstractCaseModel):
    # ... campos existentes ...
    
    # Substituir o manager padrão
    objects = CaseManager()
    
    class Meta:
        # ... meta existente ...

class Extraction(AuditedModel):
    # ... campos existentes ...
    
    objects = ExtractionManager()
```

### 2. Refatorar Views Existentes

**Antes (50+ linhas):**
```python
class CaseListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        # 20+ linhas de filtros e consultas
        
    def get_context_data(self, **kwargs):
        # 15+ linhas de contexto
        
    # Mais métodos...
```

**Depois (5 linhas):**
```python
class CaseListView(BaseListView):
    model = Case
    service_class = CaseService
    search_form_class = CaseSearchForm
    template_name = 'cases/case_list.html'
```

### 3. Migrar Lógica para Services

**Identifique lógica de negócio nas views:**
- Validações customizadas
- Operações de criação/atualização complexas
- Cálculos e estatísticas
- Mudanças de status

**Mova para services:**
```python
# Antes: Na view
def complete_registration(self, request, pk):
    case = get_object_or_404(Case, pk=pk)
    # 30+ linhas de lógica
    
# Depois: No service
def complete_registration(self, case_pk: int, create_extractions: bool = False) -> Case:
    # Lógica centralizada e testável
```

### 4. Implementar APIs

Com a lógica centralizada, criar APIs é trivial:

```python
# apps/api/views.py
class CaseViewSet(BaseAPIViewSet):
    serializer_class = CaseSerializer
    service_class = CaseService
    
    # Herda automaticamente CRUD completo!
```

## Roadmap de Implementação

### Fase 1: Infraestrutura (1-2 semanas)
1. ✅ Criar estrutura base (services, managers, mixins)
2. ✅ Implementar BaseService e BaseAPIViewSet
3. ✅ Criar managers customizados para models principais

### Fase 2: Refatoração Gradual (2-4 semanas)
1. **Casos (Cases)**
   - Migrar CaseService
   - Refatorar views principais
   - Implementar API endpoints
   
2. **Extrações (Extractions)**
   - Migrar ExtractionService
   - Refatorar operações de workflow
   - Testes unitários

3. **Base Tables**
   - Services para tabelas de apoio
   - APIs read-only
   - Endpoints de busca

### Fase 3: Otimização (1-2 semanas)
1. Performance tuning nos managers
2. Cache estratégico
3. Documentação da API

## Benefícios Imediatos

### Para Desenvolvimento Web
- **90% menos código** nas views
- **Consistência** entre funcionalidades
- **Testes** mais simples e focados
- **Manutenibilidade** melhorada

### Para APIs Futuras
- **Reutilização total** da lógica de negócio
- **Endpoints padronizados** automaticamente
- **Validações consistentes** entre web e API
- **Documentação automática** (Swagger/OpenAPI)

### Para Equipe
- **Curva de aprendizado** reduzida
- **Padrões claros** para novos recursos
- **Code review** mais eficiente
- **Debugging** simplificado

## Exemplos Práticos

### Consultas Otimizadas
```python
# Antes: Consulta ingênua
cases = Case.objects.all()

# Depois: Consulta otimizada
cases = Case.objects.with_related_data().with_statistics()
```

### Lógica Reutilizável
```python
# Service usado tanto na web quanto na API
service = CaseService(user=request.user)
case = service.complete_registration(case_id, create_extractions=True)

# Na view web
return redirect('cases:detail', pk=case.pk)

# Na API
return Response(CaseSerializer(case).data, status=201)
```

### Testes Simplificados
```python
def test_case_completion():
    service = CaseService(user=self.user)
    case = service.complete_registration(self.case.pk)
    
    assert case.status == Case.CASE_STATUS_WAITING_EXTRACTOR
    # Teste direto da lógica, sem complexidade de views
```

## Considerações de Performance

### Managers Otimizados
- `select_related()` e `prefetch_related()` automáticos
- Queries especializadas por contexto
- Filtros inteligentes com indexes

### Cache Estratégico
```python
# Cache em services para dados frequentes
@cached_property
def get_case_statistics(self, case):
    # Cálculos pesados cacheados
```

### Lazy Loading
- Services carregam dados sob demanda
- QuerySets otimizados por contexto de uso

## Próximos Passos

1. **Implementar gradualmente** - comece com Cases
2. **Manter compatibilidade** - views antigas funcionam lado a lado
3. **Testar extensivamente** - cada service deve ter testes unitários
4. **Documentar APIs** - usar DRF spectacular para docs automáticas
5. **Treinar equipe** - nos novos padrões e estrutura

Esta arquitetura prepara seu projeto para crescimento, facilita manutenção e permite expansão para APIs REST com mínimo esforço adicional.