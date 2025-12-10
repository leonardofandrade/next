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
        match = re.match(r'^([A-Z]{1,10})\s+([0-9/]+)', procedure_text, re.IGNORECASE)
        if not match:
            match = re.match(r'^([A-Z]{1,10})', procedure_text, re.IGNORECASE)
            if match:
                acronym = match.group(1).upper()
                procedure_number = procedure_text.replace(acronym, '').strip()
            else:
                errors.append(f"Não foi possível parsear: {procedure_text}")
                continue
        else:
            acronym = match.group(1).upper()
            procedure_number = match.group(2).strip()
        
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

