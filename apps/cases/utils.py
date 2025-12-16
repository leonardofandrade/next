"""
Utility functions for cases app
"""
import re
from typing import List
from django.contrib.auth.models import User
from apps.cases.models import Case, CaseProcedure
from apps.base_tables.models import ProcedureCategory


def parse_request_procedures(request_procedures_text: str, case: Case, user: User) -> List[str]:
    """
    Tenta parsear o campo request_procedures e criar CaseProcedure.
    Retorna uma lista de erros encontrados (se houver).
    
    Args:
        request_procedures_text: Texto com os procedimentos (ex: "IP 123/2024, PJ 456/2024")
        case: Instância do Case para associar os procedimentos
        user: Usuário que está criando os procedimentos (para created_by)
    
    Returns:
        List[str]: Lista de erros encontrados durante o parsing
    """
    errors = []
    if not request_procedures_text:
        return errors
    
    procedures_text = request_procedures_text.strip()
    if not procedures_text:
        return errors
    
    # Tenta dividir por vírgula ou ponto e vírgula
    procedures_list = re.split(r'[,;]', procedures_text)
    
    for procedure_text in procedures_list:
        procedure_text = procedure_text.strip()
        if not procedure_text:
            continue
        
        # Tenta extrair o acrônimo e o número
        # Primeiro identifica o acrônimo (1-10 letras maiúsculas) no início
        acronym_match = re.match(r'^([A-Z]{1,10})', procedure_text, re.IGNORECASE)
        if not acronym_match:
            errors.append(f"Não foi possível identificar acrônimo em: {procedure_text}")
            continue
        
        acronym = acronym_match.group(1).upper()
        
        # Remove o acrônimo do início do texto e pega tudo que sobrar como número
        # Isso garante que capturamos hífens, pontos, barras, etc.
        procedure_number = procedure_text[len(acronym):].strip()
        
        # Se não houver número após o acrônimo, pula
        if not procedure_number:
            errors.append(f"Não foi possível extrair número do procedimento: {procedure_text}")
            continue
        
        # Busca ProcedureCategory pelo acronym
        try:
            procedure_category = ProcedureCategory.objects.filter(
                acronym__iexact=acronym,
                deleted_at__isnull=True
            ).first()
            
            if not procedure_category:
                errors.append(f"Categoria de procedimento não encontrada para acrônimo: {acronym}")
                continue
            
            # Cria o CaseProcedure
            CaseProcedure.objects.create(
                case=case,
                number=procedure_number if procedure_number else None,
                procedure_category=procedure_category,
                created_by=user
            )
        except Exception as e:
            errors.append(f"Erro ao criar procedimento {acronym} {procedure_number}: {str(e)}")
            continue
    
    return errors

