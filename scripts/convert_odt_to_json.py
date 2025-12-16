"""
Script auxiliar para converter arquivos ODT em base64 e adicionar ao JSON de templates.
Uso: python scripts/convert_odt_to_json.py <arquivo.odt> <extraction_unit_acronym> <nome_template>
"""
import sys
import json
import base64
from pathlib import Path

def convert_odt_to_base64(odt_path):
    """Converte arquivo ODT para base64"""
    with open(odt_path, 'rb') as f:
        content = f.read()
    return base64.b64encode(content).decode('utf-8')

def update_templates_json(odt_path, extraction_unit_acronym, template_name, description=None, is_default=False):
    """Atualiza o arquivo JSON de templates com o novo template"""
    json_path = Path('initial_data/14_dispatch_templates.json')
    
    # Carrega JSON existente
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
    else:
        templates = []
    
    # Converte ODT para base64
    template_base64 = convert_odt_to_base64(odt_path)
    
    # Cria novo template
    new_template = {
        "extraction_unit_acronym": extraction_unit_acronym,
        "name": template_name,
        "description": description or f"Template {template_name} para {extraction_unit_acronym}",
        "template_filename": Path(odt_path).name,
        "template_file_base64": template_base64,
        "is_active": True,
        "is_default": is_default
    }
    
    # Adiciona ao array
    templates.append(new_template)
    
    # Salva JSON atualizado
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)
    
    print(f"Template '{template_name}' adicionado ao arquivo {json_path}")
    print(f"Tamanho do arquivo base64: {len(template_base64)} caracteres")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Uso: python scripts/convert_odt_to_json.py <arquivo.odt> <extraction_unit_acronym> <nome_template> [descrição] [--default]")
        sys.exit(1)
    
    odt_path = sys.argv[1]
    extraction_unit_acronym = sys.argv[2]
    template_name = sys.argv[3]
    description = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else None
    is_default = '--default' in sys.argv
    
    if not Path(odt_path).exists():
        print(f"Erro: Arquivo {odt_path} não encontrado")
        sys.exit(1)
    
    update_templates_json(odt_path, extraction_unit_acronym, template_name, description, is_default)
