# Templates de Ofícios (Dispatch Templates)

Este documento explica como criar e carregar templates de ofícios de resposta no sistema.

## Estrutura do JSON

O arquivo `initial_data/14_dispatch_templates.json` contém os templates de ofício que serão carregados no sistema. Cada template deve seguir a seguinte estrutura:

```json
{
  "extraction_unit_acronym": "CEINS/NEXT",
  "name": "Template Padrão NEXT",
  "description": "Descrição do template",
  "template_filename": "template.odt",
  "template_file_base64": "<conteúdo_base64_do_arquivo_odt>",
  "is_active": true,
  "is_default": true
}
```

### Campos

- **extraction_unit_acronym**: Sigla da unidade de extração (deve existir no sistema)
- **name**: Nome identificador do template
- **description**: Descrição opcional do template
- **template_filename**: Nome original do arquivo ODT
- **template_file_base64**: Conteúdo do arquivo ODT codificado em base64
- **is_active**: Se o template está ativo (padrão: `true`)
- **is_default**: Se este é o template padrão para a unidade (padrão: `false`)

## Variáveis Disponíveis nos Templates

Ao criar um template ODT, você pode usar as seguintes variáveis que serão substituídas automaticamente:

- `{{dispatch_number}}` - Número do ofício (ex: 001)
- `{{dispatch_number_formatted}}` - Número formatado (ex: 001_2025)
- `{{dispatch_full_number}}` - Número completo (ex: Ofício 001_2025 NEXT)
- `{{year}}` - Ano atual
- `{{date}}` - Data atual formatada (dd/mm/yyyy)
- `{{case_number}}` - Número do processo
- `{{requester_unit}}` - Nome da unidade solicitante
- `{{requester_unit_acronym}}` - Sigla da unidade solicitante
- `{{extraction_unit}}` - Nome da unidade de extração
- `{{extraction_unit_acronym}}` - Sigla da unidade de extração
- `{{incharge_name}}` - Nome do responsável
- `{{incharge_position}}` - Cargo do responsável

**Nota**: Por compatibilidade, também funcionam os nomes antigos com `oficio_` em vez de `dispatch_`.

## Como Adicionar um Template

### Método 1: Usando o Script Auxiliar

1. Prepare seu arquivo ODT com as variáveis necessárias
2. Execute o script de conversão:

```bash
python scripts/convert_odt_to_json.py \
  "oficios_exemplos/Ofício 001_2025 NEXT - 1DHPP - encaminhando material e dados.odt" \
  "CEINS/NEXT" \
  "Template Padrão NEXT" \
  "Template padrão para ofícios" \
  --default
```

O script irá:
- Converter o arquivo ODT para base64
- Adicionar o template ao arquivo JSON
- Marcar como padrão se usar a flag `--default`

### Método 2: Manualmente

1. Converta seu arquivo ODT para base64:

```python
import base64

with open('seu_template.odt', 'rb') as f:
    content = f.read()
    base64_content = base64.b64encode(content).decode('utf-8')
    print(base64_content)
```

2. Adicione o template ao arquivo `initial_data/14_dispatch_templates.json`:

```json
{
  "extraction_unit_acronym": "CEINS/NEXT",
  "name": "Meu Template",
  "description": "Descrição do template",
  "template_filename": "meu_template.odt",
  "template_file_base64": "<cole_o_base64_aqui>",
  "is_active": true,
  "is_default": false
}
```

## Carregando Templates no Sistema

Após adicionar os templates ao arquivo JSON, carregue-os no sistema:

```bash
# Carregar apenas os templates
python manage.py load_initial_data --file 14_dispatch_templates.json

# Ou carregar todos os dados iniciais (incluindo templates)
python manage.py load_initial_data
```

## Gerenciando Templates via Interface

Após carregar os templates, você pode gerenciá-los através da interface administrativa do Django ou através das views de gerenciamento de templates (se implementadas).

## Exemplo Completo

```json
[
  {
    "extraction_unit_acronym": "CEINS/NEXT",
    "name": "Template Padrão NEXT",
    "description": "Template padrão para ofícios de resposta da unidade CEINS/NEXT",
    "template_filename": "template_padrao_next.odt",
    "template_file_base64": "UEsDBBQAAAgAAIqAI1pexjIMJwAAACcAAAAIAAAAbWltZXR5cGVhcHBsaWNhdGlvbi92bmQub2FzaXMub3BlbmRvY3VtZW50LnRleHRQSwMEFAAACAAAioAjWgAAAAAAAAAAAAAAABoAAABDb25maWd1cmF0aW9uczIvcG9wdXBtZW51L1BLAwQUAAAIAACKgCNaAAAA...",
    "is_active": true,
    "is_default": true
  },
  {
    "extraction_unit_acronym": "SEINT/CRATO",
    "name": "Template CRATO",
    "description": "Template específico para a unidade SEINT/CRATO",
    "template_filename": "template_crato.odt",
    "template_file_base64": "...",
    "is_active": true,
    "is_default": true
  }
]
```

## Observações

- Apenas um template pode ser marcado como `is_default: true` por unidade de extração
- Templates inativos (`is_active: false`) não serão usados na geração automática
- Se não houver template configurado, o sistema gerará um ofício básico automaticamente
- O arquivo ODT deve estar no formato OpenDocument Text (.odt)
