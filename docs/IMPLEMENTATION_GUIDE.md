# Implementação Prática: Refatoração Step-by-Step

## Como Começar - Guia Prático

### 1. Adicionar nova estrutura ao settings.py

```python
# config/settings.py
INSTALLED_APPS = [
    # ... apps existentes ...
    'apps.api',  # Adicionar o novo app de API
    
    # Caso queira usar DRF futuramente
    'rest_framework',
    'rest_framework.authtoken',
]

# Configuração DRF (opcional, para futuras APIs)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}
```

### 2. Atualizar Model Case (Exemplo)

```python
# apps/cases/models.py
from apps.core.managers import CaseManager

class Case(AbstractCaseModel):
    # ... campos existentes ...
    
    # Adicionar o manager customizado
    objects = CaseManager()
    
    # Manter o resto igual
```

### 3. Criar primeiro Service

```python
# apps/cases/services.py
from apps.core.services.case_services import CaseService

# O service já está implementado em core.services.case_services
# Basta importar e usar
```

### 4. Refatorar uma View por vez

**Escolha a CaseListView primeiro:**

```python
# apps/cases/views.py

# Imports novos
from apps.core.mixins.views import BaseListView
from apps.core.services.case_services import CaseService

# Substituir a view existente
class CaseListView(BaseListView):
    model = Case
    service_class = CaseService
    search_form_class = CaseSearchForm
    template_name = 'cases/case_list.html'
    context_object_name = 'cases'
    paginate_by = 25

# Comentar ou remover a implementação antiga
# class CaseListView(LoginRequiredMixin, ListView):
#     ... implementação antiga ...
```

### 5. Testar cada mudança

```python
# tests/test_case_service.py
from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.services.case_services import CaseService
from apps.cases.models import Case

class CaseServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com')
        self.service = CaseService(user=self.user)
    
    def test_create_case(self):
        data = {
            'number': '001',
            'year': 2025,
            'status': 'draft',
            'requester_name': 'Test User'
        }
        
        case = self.service.create(data)
        
        self.assertEqual(case.number, '001')
        self.assertEqual(case.created_by, self.user)
```

## Cronograma de Migração Sugerido

### Semana 1: Preparação
- [ ] Criar estrutura base (já feito nos arquivos acima)
- [ ] Adicionar ao settings.py
- [ ] Instalar dependências se necessário
- [ ] Criar testes básicos

### Semana 2: Cases
- [ ] Atualizar model Case com manager
- [ ] Refatorar CaseListView
- [ ] Refatorar CaseDetailView  
- [ ] Refatorar CaseCreateView
- [ ] Testar todas as funcionalidades

### Semana 3: Extractions
- [ ] Implementar ExtractionService
- [ ] Refatorar views de workflow (assign, start, complete)
- [ ] Testar operações de extração

### Semana 4: Base Tables
- [ ] Services para tabelas de apoio
- [ ] Refatorar views CRUD simples
- [ ] Criar APIs básicas

## Comandos para Começar

```bash
# 1. Criar migração se necessário (caso tenha mudado models)
python manage.py makemigrations

# 2. Aplicar migrações
python manage.py migrate

# 3. Criar testes
python manage.py test apps.cases.tests.test_services

# 4. Executar servidor
python manage.py runserver
```

## Checklist de Validação

Para cada view refatorada, verificar:

- [ ] ✅ Funcionalidade mantida (mesma tela, mesmas ações)
- [ ] ✅ Permissões funcionando (staff required, etc)
- [ ] ✅ Mensagens de sucesso/erro aparecem
- [ ] ✅ Redirecionamentos funcionam
- [ ] ✅ Filtros e busca funcionam
- [ ] ✅ Performance igual ou melhor

## Rollback Plan

Caso algo dê errado:

1. **Manter views antigas comentadas** (não deletar)
2. **Usar git branches** para cada refatoração
3. **Testar em ambiente de desenvolvimento** primeiro

```python
# Rollback rápido - descomentar view antiga
# class CaseListView(LoginRequiredMixin, ListView):
#     ... implementação antiga segura ...

# Comentar view nova temporariamente
# class CaseListView(BaseListView):
#     ... nova implementação ...
```

## Benefícios Mensuráveis

Após refatoração completa:

- **Redução de código**: ~70% menos linhas nas views
- **Performance**: Consultas otimizadas (mensurar com Django Debug Toolbar)
- **Manutenibilidade**: Lógica centralizada em services  
- **APIs**: Endpoints REST criados em minutos
- **Testes**: Cobertura de testes mais simples e completa

## Próximas Funcionalidades Facilitadas

Com essa arquitetura, implementar será muito mais fácil:

1. **API REST completa** - 5 minutos por endpoint
2. **Export de dados** - CSV, Excel, PDF reutilizando services
3. **Relatórios avançados** - usando managers otimizados
4. **Integração com sistemas externos** - lógica já centralizada
5. **Mobile app** - mesma API para web e mobile
6. **Webhooks** - notificações automáticas usando services

A refatoração é um investimento que vai economizar centenas de horas no futuro!