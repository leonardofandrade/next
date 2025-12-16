"""
Serviço para geração de ofícios de resposta
"""
from typing import Optional, Dict, Any
from django.utils import timezone
from django.db import transaction
from io import BytesIO
from odf.opendocument import load, OpenDocumentText
from odf.text import P, H, Span
from odf.style import Style, TextProperties
import re
import locale

from apps.core.models import ExtractionUnit, DispatchSequenceNumber, DispatchTemplate
from apps.cases.models import Case
from apps.core.services.base import BaseService, ServiceException


class DispatchService(BaseService):
    """
    Serviço para gerenciar ofícios de resposta
    """
    
    def get_next_dispatch_number(self, extraction_unit: ExtractionUnit, year: Optional[int] = None) -> int:
        """
        Obtém o próximo número sequencial de ofício para uma extraction unit.
        
        Args:
            extraction_unit: Unidade de extração
            year: Ano (padrão: ano atual)
            
        Returns:
            Próximo número sequencial
        """
        if year is None:
            year = timezone.now().year
        
        return DispatchSequenceNumber.get_next_number(extraction_unit, year)
    
    def get_template(self, extraction_unit: ExtractionUnit, template_name: Optional[str] = None) -> Optional[DispatchTemplate]:
        """
        Obtém o template de ofício para uma extraction unit.
        
        Args:
            extraction_unit: Unidade de extração
            template_name: Nome do template (opcional, usa o padrão se não informado)
            
        Returns:
            Template de ofício ou None
        """
        if template_name:
            try:
                return DispatchTemplate.objects.get(
                    extraction_unit=extraction_unit,
                    name=template_name,
                    is_active=True
                )
            except DispatchTemplate.DoesNotExist:
                return None
        
        # Busca template padrão
        try:
            return DispatchTemplate.objects.get(
                extraction_unit=extraction_unit,
                is_default=True,
                is_active=True
            )
        except DispatchTemplate.DoesNotExist:
            # Busca qualquer template ativo
            return DispatchTemplate.objects.filter(
                extraction_unit=extraction_unit,
                is_active=True
            ).first()
    
    def generate_dispatch(self, case: Case, template: Optional[DispatchTemplate] = None) -> Dict[str, Any]:
        """
        Gera um ofício de resposta para um caso.
        
        Args:
            case: Caso para o qual gerar o ofício
            template: Template a ser usado (opcional, busca automaticamente se não informado)
            
        Returns:
            Dicionário com informações do ofício gerado (número, data, arquivo)
        """
        if not case.extraction_unit:
            raise ServiceException("Caso não possui unidade de extração associada")
        
        # Obtém template
        if not template:
            template = self.get_template(case.extraction_unit)
        
        # Obtém próximo número
        year = timezone.now().year
        dispatch_number = self.get_next_dispatch_number(case.extraction_unit, year)
        
        # Gera o arquivo ODT
        if template and template.template_file:
            # Usa template existente
            odt_file = self._generate_from_template(case, template, dispatch_number, year)
        else:
            # Gera template básico (mesmo sem template configurado)
            # Isso permite gerar ofícios mesmo sem template específico da unidade
            odt_file = self._generate_basic_dispatch(case, dispatch_number, year)
        
        # Formata número do ofício
        formatted_number = f"{dispatch_number:03d}_{year}"
        
        return {
            'number': formatted_number,
            'full_number': f"Ofício {formatted_number} {case.extraction_unit.acronym}",
            'date': timezone.now().date(),
            'file': odt_file,
            'filename': f"Ofício {formatted_number} {case.extraction_unit.acronym} - {case.requester_agency_unit.acronym if case.requester_agency_unit and case.requester_agency_unit.acronym else case.requester_agency_unit.name if case.requester_agency_unit else 'UNIDADE'} - encaminhando material e dados.odt",
            'content_type': 'application/vnd.oasis.opendocument.text'
        }
    
    def _generate_from_template(self, case: Case, template: DispatchTemplate, dispatch_number: int, year: int) -> bytes:
        """
        Gera ofício a partir de um template ODT existente.
        
        Args:
            case: Caso
            template: Template ODT
            oficio_number: Número do ofício
            year: Ano
            
        Returns:
            Arquivo ODT em bytes
        """
        # Carrega template
        template_bytes = BytesIO(template.template_file)
        doc = load(template_bytes)
        
        # Substitui variáveis no template
        self._replace_template_variables(doc, case, dispatch_number, year)
        
        # Salva em bytes
        output = BytesIO()
        doc.write(output)
        return output.getvalue()
    
    def _generate_basic_dispatch(self, case: Case, dispatch_number: int, year: int) -> bytes:
        """
        Gera ofício básico sem template.
        
        Args:
            case: Caso
            oficio_number: Número do ofício
            year: Ano
            
        Returns:
            Arquivo ODT em bytes
        """
        doc = OpenDocumentText()
        
        # Header
        h = H(outlinelevel=1, stylename="Heading")
        h.addText("S.S.P.D.S. CEARÁ")
        doc.text.addElement(h)
        
        h2 = H(outlinelevel=2, stylename="Heading")
        h2.addText("SECRETARIA DA SEGURANÇA PÚBLICA E DEFESA SOCIAL")
        doc.text.addElement(h2)
        
        h3 = H(outlinelevel=2, stylename="Heading")
        h3.addText("COORDENADORIA DE INTELIGÊNCIA")
        doc.text.addElement(h3)
        
        p = P()
        p.addText("Célula de Inteligência de Sinais - Núcleo de Extrações")
        doc.text.addElement(p)
        
        # Número do ofício
        extraction_unit_acronym = case.extraction_unit.acronym if case.extraction_unit else 'NEXT'
        formatted_number = f"{dispatch_number:03d}_{year}"
        
        p = P()
        p.addText(f"Ofício Nº {formatted_number} - {extraction_unit_acronym}")
        doc.text.addElement(p)
        
        # Data
        p = P()
        p.addText(f"Fortaleza, {timezone.now().strftime('%d de %B de %Y')}")
        doc.text.addElement(p)
        
        # Destinatário
        if case.requester_agency_unit:
            p = P()
            p.addText(f"Ao(à) {case.requester_agency_unit.name}")
            doc.text.addElement(p)
        
        # Corpo do ofício
        p = P()
        p.addText("Encaminhamos material e dados extraídos conforme solicitação.")
        doc.text.addElement(p)
        
        # Processo
        if case.number:
            p = P()
            p.addText(f"Processo: {case.number}")
            doc.text.addElement(p)
        
        # Assinatura
        if case.extraction_unit.incharge_name:
            p = P()
            p.addText(case.extraction_unit.incharge_name)
            doc.text.addElement(p)
            if case.extraction_unit.incharge_position:
                p = P()
                p.addText(case.extraction_unit.incharge_position)
                doc.text.addElement(p)
        
        # Salva em bytes
        output = BytesIO()
        doc.write(output)
        return output.getvalue()
    
    def _replace_template_variables(self, doc: OpenDocumentText, case: Case, dispatch_number: int, year: int):
        """
        Substitui variáveis no template ODT.
        
        Variáveis disponíveis:
        - {{dispatch_number}}: Número do ofício (ex: 001)
        - {{dispatch_number_formatted}}: Número formatado (ex: 001_2025)
        - {{dispatch_full_number}}: Número completo (ex: Ofício 001_2025 NEXT)
        - {{year}}: Ano atual
        - {{date}}: Data atual formatada
        - {{case_number}}: Número do processo
        - {{requester_unit}}: Nome da unidade solicitante
        - {{requester_unit_acronym}}: Sigla da unidade solicitante
        - {{extraction_unit}}: Nome da unidade de extração
        - {{extraction_unit_acronym}}: Sigla da unidade de extração
        - {{incharge_name}}: Nome do responsável
        - {{incharge_position}}: Cargo do responsável
        
        Args:
            doc: Documento ODT
            case: Caso
            dispatch_number: Número do ofício
            year: Ano
        """
        # Prepara variáveis
        variables = {
            'dispatch_number': f"{dispatch_number:03d}",
            'dispatch_number_formatted': f"{dispatch_number:03d}_{year}",
            'dispatch_full_number': f"Ofício {dispatch_number:03d}_{year} {case.extraction_unit.acronym if case.extraction_unit else 'NEXT'}",
            # Mantém compatibilidade com nomes antigos
            'oficio_number': f"{dispatch_number:03d}",
            'oficio_number_formatted': f"{dispatch_number:03d}_{year}",
            'oficio_full_number': f"Ofício {dispatch_number:03d}_{year} {case.extraction_unit.acronym if case.extraction_unit else 'NEXT'}",
            'year': str(year),
            'date': timezone.now().strftime('%d/%m/%Y'),
            'case_number': case.number or str(case.pk),
            'requester_unit': case.requester_agency_unit.name if case.requester_agency_unit else '',
            'requester_unit_acronym': case.requester_agency_unit.acronym if case.requester_agency_unit and case.requester_agency_unit.acronym else case.requester_agency_unit.name if case.requester_agency_unit else '',
            'extraction_unit': case.extraction_unit.name if case.extraction_unit else '',
            'extraction_unit_acronym': case.extraction_unit.acronym if case.extraction_unit else 'NEXT',
            'incharge_name': case.extraction_unit.incharge_name if case.extraction_unit else '',
            'incharge_position': case.extraction_unit.incharge_position if case.extraction_unit else '',
        }
        
        # Substitui em todos os parágrafos
        for para in doc.getElementsByType(P):
            text = para.textContent
            if text:
                for key, value in variables.items():
                    text = text.replace(f"{{{{{key}}}}}", str(value))
                    text = text.replace(f"{{{{ {key} }}}}", str(value))  # Com espaços
                # Atualiza o texto do parágrafo
                para.textContent = text
        
        # Substitui em headings também
        from odf.text import H
        for heading in doc.getElementsByType(H):
            text = heading.textContent
            if text:
                for key, value in variables.items():
                    text = text.replace(f"{{{{{key}}}}}", str(value))
                    text = text.replace(f"{{{{ {key} }}}}", str(value))
                heading.textContent = text
