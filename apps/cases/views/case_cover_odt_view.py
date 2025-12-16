"""
View para gerar capa do processo em formato ODT
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import View
from django.http import HttpResponse
from io import BytesIO

from apps.cases.models import Case
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties, TableCellProperties, TableProperties, TableColumnProperties
from odf.text import P, H, Span
from odf.table import Table, TableRow, TableCell, TableColumn
from odf import style


class CaseCoverODTView(LoginRequiredMixin, View):
    """
    Gera ODT da capa do processo para edição
    """
    
    def get(self, request, pk):
        """
        Gera o ODT da capa do processo
        """
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o cadastro foi finalizado
        if not case.registration_completed_at:
            messages.error(
                request,
                'A capa do processo só pode ser gerada após a finalização do cadastro.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        # Busca dispositivos do caso
        devices = case.case_devices.filter(deleted_at__isnull=True).select_related(
            'device_category',
            'device_model__brand'
        )
        
        # Busca procedimentos do caso
        procedures = case.procedures.filter(deleted_at__isnull=True).select_related(
            'procedure_category'
        )
        
        # Prepara dados para tramitações (baseado em eventos do processo)
        tramitacoes = []
        
        # Tramitação inicial: recebimento do processo (da delegacia para NEXT)
        if case.created_at:
            origem_nome = case.requester_agency_unit.name if case.requester_agency_unit else 'DM BARREIRA'
            if case.requester_agency_unit and case.requester_agency_unit.acronym:
                origem_nome = case.requester_agency_unit.acronym
            tramitacoes.append({
                'de': origem_nome,
                'para': case.extraction_unit.acronym if case.extraction_unit else 'NEXT/COIN',
                'data': case.created_at.strftime('%d/%m/%Y'),
                'responsavel': case.created_by.get_full_name() if case.created_by and case.created_by.get_full_name() else (case.created_by.username if case.created_by else 'N/A')
            })
        
        # Tramitação: devolução/finalização (de NEXT para a delegacia)
        if case.finished_at:
            destino_nome = case.requester_agency_unit.name if case.requester_agency_unit else 'BARREIRA'
            if case.requester_agency_unit and case.requester_agency_unit.acronym:
                destino_nome = case.requester_agency_unit.acronym
            tramitacoes.append({
                'de': 'NEXT',
                'para': destino_nome,
                'data': case.finished_at.strftime('%d/%m/%Y'),
                'responsavel': case.finished_by.get_full_name() if case.finished_by and case.finished_by.get_full_name() else (case.finished_by.username if case.finished_by else 'N/A')
            })
        elif case.assigned_at and case.assigned_to:
            destino_nome = case.requester_agency_unit.name if case.requester_agency_unit else 'BARREIRA'
            if case.requester_agency_unit and case.requester_agency_unit.acronym:
                destino_nome = case.requester_agency_unit.acronym
            tramitacoes.append({
                'de': 'NEXT',
                'para': destino_nome,
                'data': case.assigned_at.strftime('%d/%m/%Y'),
                'responsavel': case.assigned_to.get_full_name() if case.assigned_to.get_full_name() else case.assigned_to.username
            })
        
        # Busca documentos do caso
        documents = case.documents.filter(deleted_at__isnull=True).select_related(
            'document_category'
        )
        
        # Busca todos os Ofícios de Solicitação (OFS) nos documentos
        ofs_documents = documents.filter(
            document_category__acronym__iexact='OFS'
        ) if documents else []
        
        # Cria documento ODT
        try:
            doc = OpenDocumentText()
            
            # Estilos de texto
            bold_style = Style(name="BoldStyle", family="text")
            bold_style.addElement(TextProperties(fontweight="bold"))
            doc.styles.addElement(bold_style)
            
            # Estilo para número do documento (fundo cinza, centralizado, borda)
            doc_number_style = Style(name="DocNumberStyle", family="paragraph")
            doc_number_style.addElement(ParagraphProperties(
                backgroundcolor="#d3d3d3",
                textalign="center",
                border="0.03cm solid #999999",
                padding="0.28cm 0.53cm"
            ))
            doc_number_style.addElement(TextProperties(
                fontsize="16pt",
                fontweight="bold"
            ))
            doc.styles.addElement(doc_number_style)
            
            # Estilo para título de box
            box_title_style = Style(name="BoxTitleStyle", family="paragraph")
            box_title_style.addElement(TextProperties(
                fontsize="11pt",
                fontweight="bold"
            ))
            box_title_style.addElement(ParagraphProperties(
                marginbottom="0.2cm"
            ))
            doc.styles.addElement(box_title_style)
            
            # Estilo para conteúdo de box
            box_content_style = Style(name="BoxContentStyle", family="paragraph")
            box_content_style.addElement(TextProperties(
                fontsize="10pt"
            ))
            box_content_style.addElement(ParagraphProperties(
                marginbottom="0.1cm"
            ))
            doc.styles.addElement(box_content_style)
            
            # Estilo para célula de box (fundo cinza claro, borda)
            box_cell_style = Style(name="BoxCellStyle", family="table-cell")
            box_cell_style.addElement(TableCellProperties(
                backgroundcolor="#f5f5f5",
                border="0.03cm solid #999999",
                padding="0.35cm"
            ))
            doc.styles.addElement(box_cell_style)
            
            # Estilo para célula de tabela com fundo cinza (header)
            table_header_cell_style = Style(name="TableHeaderCellStyle", family="table-cell")
            table_header_cell_style.addElement(TableCellProperties(
                backgroundcolor="#e0e0e0",
                border="0.03cm solid #999999"
            ))
            table_header_cell_style.addElement(ParagraphProperties(
                padding="0cm"
            ))
            table_header_cell_style.addElement(TextProperties(
                fontweight="bold"
            ))
            doc.styles.addElement(table_header_cell_style)
            
            # Estilo para célula de tabela normal
            table_cell_style = Style(name="TableCellStyle", family="table-cell")
            table_cell_style.addElement(TableCellProperties(
                border="0.03cm solid #999999"
            ))
            table_cell_style.addElement(ParagraphProperties(
                padding="0cm"
            ))
            doc.styles.addElement(table_cell_style)
            
            # Estilo para tabela de tramitações (box)
            tramitacoes_table_style = Style(name="TramitacoesTableStyle", family="table")
            tramitacoes_table_style.addElement(TableProperties(
                width="100%"
            ))
            doc.styles.addElement(tramitacoes_table_style)
            
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
            
            # Número do documento (com estilo de box)
            extraction_unit_acronym = case.extraction_unit.acronym if case.extraction_unit and case.extraction_unit.acronym else 'NEXT'
            doc_number = f"{case.number or case.pk} - {extraction_unit_acronym}"
            
            p = P(stylename=doc_number_style)
            p.addText(doc_number)
            doc.text.addElement(p)
            
            # Assunto (box) - usando tabela de 1 célula para criar o box
            box_table = Table()
            col = TableColumn()
            box_table.addElement(col)
            box_row = TableRow()
            box_cell = TableCell()
            box_cell.setAttribute("stylename", "BoxCellStyle")
            
            p_title = P(stylename=box_title_style)
            p_title.addText("Assunto")
            box_cell.addElement(p_title)
            p_content = P(stylename=box_content_style)
            p_content.addText("Extração de dados")
            box_cell.addElement(p_content)
            box_row.addElement(box_cell)
            box_table.addElement(box_row)
            doc.text.addElement(box_table)
            
            # Procedimentos (box)
            if procedures:
                box_table = Table()
                col = TableColumn()
                box_table.addElement(col)
                box_row = TableRow()
                box_cell = TableCell()
                box_cell.setAttribute("stylename", "BoxCellStyle")
                
                p_title = P(stylename=box_title_style)
                p_title.addText("Procedimentos")
                box_cell.addElement(p_title)
                
                for procedure in procedures:
                    if procedure.procedure_category:
                        proc_text = procedure.procedure_category.name
                        if procedure.number:
                            proc_text += f" - {procedure.number}"
                        p_content = P(stylename=box_content_style)
                        p_content.addText(proc_text)
                        box_cell.addElement(p_content)
                
                box_row.addElement(box_cell)
                box_table.addElement(box_row)
                doc.text.addElement(box_table)
            
            # Documentos (box)
            if documents:
                box_table = Table()
                col = TableColumn()
                box_table.addElement(col)
                box_row = TableRow()
                box_cell = TableCell()
                box_cell.setAttribute("stylename", "BoxCellStyle")
                
                p_title = P(stylename=box_title_style)
                p_title.addText("Documentos")
                box_cell.addElement(p_title)
                
                for document in documents:
                    if document.document_category:
                        doc_text = document.document_category.name
                        if document.number:
                            doc_text += f" - {document.number}"
                        p_content = P(stylename=box_content_style)
                        p_content.addText(doc_text)
                        box_cell.addElement(p_content)
                
                box_row.addElement(box_cell)
                box_table.addElement(box_row)
                doc.text.addElement(box_table)
            
            # Origem (box)
            box_table = Table()
            col = TableColumn()
            box_table.addElement(col)
            box_row = TableRow()
            box_cell = TableCell()
            box_cell.setAttribute("stylename", "BoxCellStyle")
            
            p_title = P(stylename=box_title_style)
            p_title.addText("Origem")
            box_cell.addElement(p_title)
            
            p_content = P(stylename=box_content_style)
            span_label = Span(stylename=bold_style)
            span_label.addText("Unidade: ")
            p_content.addElement(span_label)
            p_content.addText(case.requester_agency_unit.name if case.requester_agency_unit else "-")
            box_cell.addElement(p_content)
            
            if case.requester_reply_email:
                p_content = P(stylename=box_content_style)
                span_label = Span(stylename=bold_style)
                span_label.addText("E-mail: ")
                p_content.addElement(span_label)
                p_content.addText(case.requester_reply_email)
                box_cell.addElement(p_content)
            
            if case.requester_authority_name:
                p_content = P(stylename=box_content_style)
                span_label = Span(stylename=bold_style)
                span_label.addText("Autoridade: ")
                p_content.addElement(span_label)
                autoridade_text = case.requester_authority_name
                if case.requester_authority_position:
                    autoridade_text += f" - {case.requester_authority_position.name}"
                p_content.addText(autoridade_text)
                box_cell.addElement(p_content)
            
            # Ofícios
            if ofs_documents:
                p_content = P(stylename=box_content_style)
                span_label = Span(stylename=bold_style)
                span_label.addText("Ofício: ")
                p_content.addElement(span_label)
                oficio_numbers = []
                for ofs_doc in ofs_documents:
                    if ofs_doc.number:
                        oficio_numbers.append(ofs_doc.number)
                p_content.addText(", ".join(oficio_numbers) if oficio_numbers else "-")
                box_cell.addElement(p_content)
            elif case.extraction_request and case.extraction_request.request_procedures:
                p_content = P(stylename=box_content_style)
                span_label = Span(stylename=bold_style)
                span_label.addText("Ofício: ")
                p_content.addElement(span_label)
                p_content.addText(case.extraction_request.request_procedures)
                box_cell.addElement(p_content)
            
            box_row.addElement(box_cell)
            box_table.addElement(box_row)
            doc.text.addElement(box_table)
            
            # Aparelhos (box)
            if devices:
                box_table = Table()
                col = TableColumn()
                box_table.addElement(col)
                box_row = TableRow()
                box_cell = TableCell()
                box_cell.setAttribute("stylename", "BoxCellStyle")
                
                p_title = P(stylename=box_title_style)
                p_title.addText(f"Aparelhos ({len(devices)})")
                box_cell.addElement(p_title)
                
                for device in devices:
                    device_text = ""
                    if device.device_model:
                        device_text = f"{device.device_model.brand.name} {device.device_model.name}"
                    else:
                        device_text = "DISPOSITIVO"
                    
                    if device.color:
                        device_text += f" - {device.color}"
                    
                    if device.imei_01:
                        device_text += f" - IMEI: {device.imei_01}"
                    
                    p_content = P(stylename=box_content_style)
                    p_content.addText(device_text)
                    box_cell.addElement(p_content)
                
                box_row.addElement(box_cell)
                box_table.addElement(box_row)
                doc.text.addElement(box_table)
            
            # Tramitações (box com tabela)
            box_table = Table()
            col = TableColumn()
            box_table.addElement(col)
            box_row = TableRow()
            box_cell = TableCell()
            box_cell.setAttribute("stylename", "BoxCellStyle")
            
            p_title = P(stylename=box_title_style)
            p_title.addText("Tramitações do Processo")
            box_cell.addElement(p_title)
            
            # Tabela de tramitações (dentro do box)
            table = Table(stylename=tramitacoes_table_style)
            
            # Colunas
            for i in range(4):
                col = TableColumn()
                table.addElement(col)
            
            # Header
            row = TableRow()
            for header in ['DE', 'PARA', 'DATA', 'RESPONSÁVEL']:
                cell = TableCell(stylename=table_header_cell_style)
                p = P()
                p.addText(header)
                cell.addElement(p)
                row.addElement(cell)
            table.addElement(row)
            
            # Dados
            if tramitacoes:
                for tramitacao in tramitacoes:
                    row = TableRow()
                    for value in [tramitacao['de'], tramitacao['para'], tramitacao['data'], tramitacao['responsavel']]:
                        cell = TableCell(stylename=table_cell_style)
                        p = P()
                        p.addText(value)
                        cell.addElement(p)
                        row.addElement(cell)
                    table.addElement(row)
            else:
                # Linha vazia
                row = TableRow()
                for i in range(4):
                    cell = TableCell(stylename=table_cell_style)
                    p = P()
                    cell.addElement(p)
                    row.addElement(cell)
                table.addElement(row)
            
            # 5 linhas vazias
            for i in range(5):
                row = TableRow()
                for j in range(4):
                    cell = TableCell(stylename=table_cell_style)
                    p = P()
                    cell.addElement(p)
                    row.addElement(cell)
                table.addElement(row)
            
            # Adiciona a tabela dentro do box
            box_cell.addElement(table)
            box_row.addElement(box_cell)
            box_table.addElement(box_row)
            doc.text.addElement(box_table)
            
            # Salva em BytesIO
            buffer = BytesIO()
            doc.write(buffer)
            odt_content = buffer.getvalue()
            buffer.close()
            
            # Retorna o ODT como resposta HTTP
            response = HttpResponse(odt_content, content_type='application/vnd.oasis.opendocument.text')
            filename = f'capa_processo_{case.number or case.pk}.odt'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            messages.error(
                request,
                f'Erro ao gerar o ODT da capa: {str(e)}'
            )
            return redirect('cases:detail', pk=case.pk)


class CaseDispatchGenerateView(LoginRequiredMixin, View):
    """
    Gera ofício de resposta para um caso
    """
    
    def post(self, request, pk):
        """
        Gera o ofício de resposta do processo
        """
        from django.shortcuts import get_object_or_404
        from django.contrib import messages
        from apps.cases.models import Case
        
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o processo está finalizado
        if case.status != Case.CASE_STATUS_COMPLETED:
            messages.error(
                request,
                'O ofício só pode ser gerado para processos finalizados.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        # Verifica se já existe ofício gerado
        if case.dispatch_number:
            messages.warning(
                request,
                f'Já existe um ofício gerado para este processo: {case.dispatch_number}. '
                'Para gerar um novo, é necessário remover o ofício existente primeiro.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        try:
            from apps.core.services.dispatch_service import DispatchService
            dispatch_service = DispatchService()
            dispatch_data = dispatch_service.generate_dispatch(case)
            
            # Atualiza o caso com os dados do ofício
            case.dispatch_number = dispatch_data['number']
            case.dispatch_date = dispatch_data['date']
            case.dispatch_file = dispatch_data['file']
            case.dispatch_filename = dispatch_data['filename']
            case.dispatch_content_type = dispatch_data['content_type']
            case.save()
            
            messages.success(
                request,
                f'Ofício {dispatch_data["number"]} gerado com sucesso!'
            )
            
        except Exception as e:
            messages.error(
                request,
                f'Erro ao gerar o ofício: {str(e)}'
            )
        
        return redirect('cases:detail', pk=case.pk)


class CaseDispatchDownloadView(LoginRequiredMixin, View):
    """
    Download do ofício de resposta de um caso
    """
    
    def get(self, request, pk):
        """
        Faz download do ofício de resposta do processo
        """
        from django.shortcuts import get_object_or_404
        from django.contrib import messages
        from django.http import HttpResponse
        from apps.cases.models import Case
        
        case = get_object_or_404(
            Case.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        if not case.dispatch_file:
            messages.error(
                request,
                'Não há ofício gerado para este processo.'
            )
            return redirect('cases:detail', pk=case.pk)
        
        response = HttpResponse(case.dispatch_file, content_type=case.dispatch_content_type or 'application/vnd.oasis.opendocument.text')
        filename = case.dispatch_filename or f'oficio_{case.dispatch_number}.odt'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
