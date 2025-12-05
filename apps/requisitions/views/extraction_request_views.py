"""
Views para o app requisitions
"""
import re
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings

from apps.requisitions.models import ExtractionRequest
from apps.requisitions.forms import ExtractionRequestForm, ExtractionRequestSearchForm
from apps.cases.models import Case, CaseProcedure
from apps.base_tables.models import ProcedureCategory


class ExtractionRequestListView(LoginRequiredMixin, ListView):
    """
    Lista todas as solicitações de extração com filtros
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_list.html'
    context_object_name = 'extraction_requests'
    paginate_by = settings.PAGINATE_BY
    
    def get_queryset(self):
        queryset = ExtractionRequest.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category',
            'created_by',
            'received_by'
        ).order_by('-requested_at', '-created_at')
        
        form = ExtractionRequestSearchForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(request_procedures__icontains=search) |
                    Q(requester_authority_name__icontains=search) |
                    Q(additional_info__icontains=search) |
                    Q(requester_agency_unit__name__icontains=search) |
                    Q(requester_agency_unit__acronym__icontains=search)
                )
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status__in=status)
            
            extraction_unit = form.cleaned_data.get('extraction_unit')
            if extraction_unit:
                queryset = queryset.filter(extraction_unit__in=extraction_unit)
            
            crime_category = form.cleaned_data.get('crime_category')
            if crime_category:
                queryset = queryset.filter(crime_category=crime_category)
            
            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(requested_at__date__gte=date_from)
            
            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(requested_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Solicitações de Extração'
        context['page_icon'] = 'fa-envelope-open-text'
        context['form'] = ExtractionRequestSearchForm(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context


class ExtractionRequestDetailView(LoginRequiredMixin, DetailView):
    """
    Exibe os detalhes de uma solicitação de extração
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_detail.html'
    context_object_name = 'extraction_request'
    
    def get_queryset(self):
        return ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-file-alt'
        return context


class ExtractionRequestCreateView(LoginRequiredMixin, CreateView):
    """
    Cria uma nova solicitação de extração
    """
    model = ExtractionRequest
    form_class = ExtractionRequestForm
    template_name = 'requisitions/extraction_request_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        extraction_request = form.save(commit=False)
        extraction_request.created_by = self.request.user
        
        # Define requested_at automaticamente se não estiver preenchido
        if not extraction_request.requested_at:
            extraction_request.requested_at = timezone.now()
        
        # Define status baseado na extraction_unit
        if extraction_request.extraction_unit:
            extraction_request.status = ExtractionRequest.REQUEST_STATUS_ASSIGNED
        else:
            extraction_request.status = ExtractionRequest.REQUEST_STATUS_PENDING
        
        extraction_request.save()
        
        messages.success(
            self.request,
            f'Solicitação #{extraction_request.pk} criada com sucesso!'
        )
        
        # Verifica qual ação foi solicitada
        save_and_add_another = self.request.POST.get('save_and_add_another')
        keep_data = self.request.POST.get('keep_data_for_new')
        
        if keep_data:
            # Checkbox marcado - mantém dados comuns
            initial_data = {
                'requester_agency_unit': extraction_request.requester_agency_unit.pk if extraction_request.requester_agency_unit else None,
                'requester_reply_email': extraction_request.requester_reply_email,
                'requester_authority_name': extraction_request.requester_authority_name,
                'requester_authority_position': extraction_request.requester_authority_position.pk if extraction_request.requester_authority_position else None,
                'crime_category': extraction_request.crime_category.pk if extraction_request.crime_category else None,
                'extraction_unit': extraction_request.extraction_unit.pk if extraction_request.extraction_unit else None,
            }
            form = ExtractionRequestForm(initial=initial_data, user=self.request.user)
            
            context = self.get_context_data(form=form)
            context['keep_data_checked'] = True
            return self.render_to_response(context)
        
        if save_and_add_another:
            # Botão "Criar e Adicionar Outra" - redireciona para formulário vazio
            return redirect('requisitions:create')
        
        return redirect('requisitions:update', pk=extraction_request.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nova Solicitação'
        context['page_icon'] = 'fa-plus'
        context['action'] = 'create'
        
        # Add distribution summary for sidebar
        from apps.requisitions.services import get_distribution_summary
        context['distribution_summary'] = get_distribution_summary()
        
        return context


class ExtractionRequestUpdateView(LoginRequiredMixin, UpdateView):
    """
    Atualiza uma solicitação de extração existente
    """
    model = ExtractionRequest
    form_class = ExtractionRequestForm
    template_name = 'requisitions/extraction_request_form.html'
    
    def get_queryset(self):
        return ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        extraction_request = form.save(commit=False)
        
        # Armazena o extraction_unit anterior para comparação
        old_extraction_unit = self.object.extraction_unit
        
        extraction_request.updated_by = self.request.user
        extraction_request.version += 1
        
        # Define requested_at automaticamente se não estiver preenchido
        if not extraction_request.requested_at:
            extraction_request.requested_at = timezone.now()
        
        # Atualiza status se extraction_unit mudou
        new_extraction_unit = extraction_request.extraction_unit
        if old_extraction_unit != new_extraction_unit:
            if new_extraction_unit:
                # Se atribuiu uma unidade, muda para 'assigned'
                if extraction_request.status == ExtractionRequest.REQUEST_STATUS_PENDING:
                    extraction_request.status = ExtractionRequest.REQUEST_STATUS_ASSIGNED
            else:
                # Se removeu a unidade, volta para 'pending'
                if extraction_request.status == ExtractionRequest.REQUEST_STATUS_ASSIGNED:
                    extraction_request.status = ExtractionRequest.REQUEST_STATUS_PENDING
        
        extraction_request.save()
        
        messages.success(
            self.request,
            f'Solicitação #{extraction_request.pk} atualizada com sucesso!'
        )
        return redirect('requisitions:detail', pk=extraction_request.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-edit'
        context['action'] = 'update'
        return context


class ExtractionRequestDeleteView(LoginRequiredMixin, DeleteView):
    """
    Realiza soft delete de uma solicitação de extração
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_confirm_delete.html'
    success_url = None
    
    def get_queryset(self):
        return ExtractionRequest.objects.filter(deleted_at__isnull=True)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.deleted_at = timezone.now()
        self.object.deleted_by = request.user
        self.object.save()
        
        messages.success(
            request,
            f'Solicitação #{self.object.pk} excluída com sucesso!'
        )
        return redirect('requisitions:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Excluir Solicitação #{self.object.pk}'
        context['page_icon'] = 'fa-trash'
        return context


class ExtractionRequestNotReceivedView(LoginRequiredMixin, ListView):
    """
    Lista solicitações não recebidas (pending ou assigned e sem received_at)
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_pending_list.html'
    context_object_name = 'extraction_requests'
    paginate_by = settings.PAGINATE_BY
    
    def get_queryset(self):
        queryset = ExtractionRequest.objects.filter(
            deleted_at__isnull=True,
            received_at__isnull=True,
            status__in=[ExtractionRequest.REQUEST_STATUS_PENDING, ExtractionRequest.REQUEST_STATUS_ASSIGNED]
        ).select_related(
            'requester_agency_unit',
            'extraction_unit',
            'requester_authority_position',
            'crime_category',
            'created_by',
            'case'
        ).order_by('-requested_at', '-created_at')
        
        form = ExtractionRequestSearchForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(request_procedures__icontains=search) |
                    Q(requester_authority_name__icontains=search) |
                    Q(additional_info__icontains=search) |
                    Q(requester_agency_unit__name__icontains=search) |
                    Q(requester_agency_unit__acronym__icontains=search)
                )
            
            status = form.cleaned_data.get('status')
            if status:
                # Filtra apenas status permitidos para esta view
                allowed_statuses = [ExtractionRequest.REQUEST_STATUS_PENDING, ExtractionRequest.REQUEST_STATUS_ASSIGNED]
                filtered_statuses = [s for s in status if s in allowed_statuses]
                if filtered_statuses:
                    queryset = queryset.filter(status__in=filtered_statuses)
            
            extraction_unit = form.cleaned_data.get('extraction_unit')
            if extraction_unit:
                queryset = queryset.filter(extraction_unit__in=extraction_unit)
            
            crime_category = form.cleaned_data.get('crime_category')
            if crime_category:
                queryset = queryset.filter(crime_category=crime_category)
            
            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(requested_at__date__gte=date_from)
            
            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(requested_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Solicitações Não Recebidas'
        context['page_icon'] = 'fa-inbox'
        context['form'] = ExtractionRequestSearchForm(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context


def parse_request_procedures(request_procedures_text, case):
    """
    Tenta parsear o campo request_procedures e criar CaseProcedure.
    Formato esperado: "IP 123/2024, PJ 456/2024" ou similar.
    Retorna uma lista de erros encontrados (se houver).
    """
    errors = []
    if not request_procedures_text:
        return errors
    
    # Remove espaços extras e divide por vírgula
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
        # Padrão: "ACRONIMO NUMERO" ou "ACRONIMO NUMERO/ANO"
        match = re.match(r'^([A-Z]{1,10})\s+([0-9/]+)', procedure_text, re.IGNORECASE)
        if not match:
            # Tenta outro padrão: pode ser só o acrônimo ou formato diferente
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
                created_by=case.created_by
            )
        except Exception as e:
            errors.append(f"Erro ao criar procedimento {acronym} {procedure_number}: {str(e)}")
            continue
    
    return errors


class CreateCaseFromRequestView(LoginRequiredMixin, View):
    """
    Cria um Case a partir de um ExtractionRequest
    """
    def post(self, request, pk):
        extraction_request = get_object_or_404(
            ExtractionRequest.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se já existe um case para esta extraction_request
        # Como é OneToOneField, verificamos se existe e não está deletado
        if hasattr(extraction_request, 'case'):
            existing_case = extraction_request.case
            if existing_case and not existing_case.deleted_at:
                messages.error(
                    request,
                    f'Já existe um processo criado para esta solicitação (Processo #{existing_case.pk}).'
                )
                return redirect('requisitions:not_received')
        
        try:
            # Cria o Case copiando os dados do ExtractionRequest
            case = Case(
                requester_agency_unit=extraction_request.requester_agency_unit,
                requested_at=extraction_request.requested_at,
                requested_device_amount=extraction_request.requested_device_amount,
                extraction_unit=extraction_request.extraction_unit,
                requester_reply_email=extraction_request.requester_reply_email,
                requester_authority_name=extraction_request.requester_authority_name,
                requester_authority_position=extraction_request.requester_authority_position,
                request_procedures=extraction_request.request_procedures,
                crime_category=extraction_request.crime_category,
                additional_info=extraction_request.additional_info,
                extraction_request=extraction_request,
                status=Case.CASE_STATUS_DRAFT,
                number=None,  # Será criado posteriormente
                created_by=request.user,
            )
            case.save()
            
            # Tenta parsear request_procedures e criar CaseProcedure
            if extraction_request.request_procedures:
                errors = parse_request_procedures(
                    extraction_request.request_procedures,
                    case
                )
                if errors:
                    # Adiciona mensagens de aviso, mas não impede a criação
                    for error in errors:
                        messages.warning(request, error)
            
            # Atualiza a ExtractionRequest: seta received_at, received_by e status
            if not extraction_request.received_at:
                extraction_request.received_at = timezone.now()
                extraction_request.received_by = request.user
            
            if extraction_request.status not in [
                ExtractionRequest.REQUEST_STATUS_ASSIGNED,
                ExtractionRequest.REQUEST_STATUS_RECEIVED
            ]:
                extraction_request.status = ExtractionRequest.REQUEST_STATUS_ASSIGNED
            
            extraction_request.updated_by = request.user
            extraction_request.version += 1
            extraction_request.save()
            
            messages.success(
                request,
                f'Processo criado com sucesso a partir da solicitação #{extraction_request.pk}!'
            )
            
            # Redireciona para o update do case
            return redirect('cases:update', pk=case.pk)
            
        except Exception as e:
            messages.error(
                request,
                f'Erro ao criar processo: {str(e)}'
            )
            return redirect('requisitions:not_received')


class GenerateReplyEmailView(LoginRequiredMixin, View):
    """
    Gera o texto de email de resposta baseado no template da extraction_unit
    """
    def get(self, request, pk):
        extraction_request = get_object_or_404(
            ExtractionRequest.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se há uma extraction_unit associada
        if not extraction_request.extraction_unit:
            # Se for requisição AJAX, retorna JSON de erro
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Esta solicitação não possui uma unidade de extração associada.'
                }, status=400)
            # Caso contrário, redireciona com mensagem
            messages.error(
                request,
                'Esta solicitação não possui uma unidade de extração associada.'
            )
            return redirect('requisitions:detail', pk=pk)
        
        extraction_unit = extraction_request.extraction_unit
        
        # Tenta obter o template das configurações primeiro, depois do modelo direto
        template = None
        subject_template = None
        
        # Tenta obter das configurações (ExtractionUnitSettings) primeiro
        try:
            if hasattr(extraction_unit, 'extraction_unit_settings'):
                settings = extraction_unit.extraction_unit_settings
                if settings and hasattr(settings, 'reply_email_template') and settings.reply_email_template:
                    template = settings.reply_email_template
                if settings and hasattr(settings, 'reply_email_subject') and settings.reply_email_subject:
                    subject_template = settings.reply_email_subject
        except Exception:
            pass
        
        # Se não encontrou nas configurações, tenta no modelo direto
        if not template and extraction_unit.reply_email_template:
            template = extraction_unit.reply_email_template
        
        if not subject_template and extraction_unit.reply_email_subject:
            subject_template = extraction_unit.reply_email_subject
        
        if not template:
            # Se for requisição AJAX, retorna JSON de erro
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'A unidade de extração não possui um template de email de resposta configurado.'
                }, status=400)
            # Caso contrário, redireciona com mensagem
            messages.error(
                request,
                'A unidade de extração não possui um template de email de resposta configurado.'
            )
            return redirect('requisitions:detail', pk=pk)
        
        # Prepara os dados para substituição
        requested_device_amount_str = str(extraction_request.requested_device_amount) if extraction_request.requested_device_amount else 'N/A'
        
        context_data = {
            'procedures': extraction_request.request_procedures or 'N/A',
            'extraction_unit_name': extraction_unit.name or '',
            'extraction_unit_acronym': extraction_unit.acronym or '',
            'extraction_unit_city': extraction_unit.city_name or '',
            'extraction_unit_state': extraction_unit.state_name or '',
            'extraction_unit_postal_code': extraction_unit.postal_code or '',
            'extraction_unit_address': extraction_unit.address_line1 or '',
            'extraction_unit_phone': extraction_unit.primary_phone or '',
            'extraction_unit_secondary_phone': extraction_unit.secondary_phone or '',
            'extraction_unit_email': extraction_unit.primary_email or '',
            'requested_device_amount': requested_device_amount_str,
            'requested_authority_position': requested_device_amount_str,  # Compatibilidade com templates antigos
            'requester_authority_name': extraction_request.requester_authority_name or '',
            'requester_authority_position': extraction_request.requester_authority_position.name if extraction_request.requester_authority_position else '',
            'requester_agency_unit': extraction_request.requester_agency_unit.name if extraction_request.requester_agency_unit else '',
        }
        
        # Substitui os placeholders no template
        email_body = template
        for key, value in context_data.items():
            placeholder = '{' + key + '}'
            email_body = email_body.replace(placeholder, str(value))
        
        # Substitui no assunto também
        email_subject = subject_template or 'Resposta à Solicitação de Extração'
        for key, value in context_data.items():
            placeholder = '{' + key + '}'
            email_subject = email_subject.replace(placeholder, str(value))
        
        # Se for requisição AJAX, retorna JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'subject': email_subject,
                'body': email_body,
                'to': extraction_request.requester_reply_email or '',
            })
        
        # Caso contrário, renderiza uma página com o texto
        return render(request, 'requisitions/generate_reply_email.html', {
            'extraction_request': extraction_request,
            'email_subject': email_subject,
            'email_body': email_body,
            'email_to': extraction_request.requester_reply_email or '',
        })


class ExtractionRequestDistributionListView(LoginRequiredMixin, ListView):
    """
    Lista solicitações de extração agrupadas por extraction_unit com resumo (distribuição)
    """
    model = ExtractionRequest
    template_name = 'requisitions/extraction_request_distribution_list.html'
    context_object_name = 'summary_data'
    
    def get_queryset(self):
        # Busca todas as solicitações não deletadas
        queryset = ExtractionRequest.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            'extraction_unit',
            'requester_agency_unit'
        )
        
        # Aplica filtros se houver
        form = ExtractionRequestSearchForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(request_procedures__icontains=search) |
                    Q(requester_authority_name__icontains=search) |
                    Q(additional_info__icontains=search) |
                    Q(requester_agency_unit__name__icontains=search) |
                    Q(requester_agency_unit__acronym__icontains=search)
                )
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status__in=status)
            
            extraction_unit = form.cleaned_data.get('extraction_unit')
            if extraction_unit:
                queryset = queryset.filter(extraction_unit__in=extraction_unit)
            
            crime_category = form.cleaned_data.get('crime_category')
            if crime_category:
                queryset = queryset.filter(crime_category=crime_category)
            
            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(requested_at__date__gte=date_from)
            
            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(requested_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = self.get_queryset()
        
        # Agrupa por extraction_unit e calcula estatísticas
        from django.db.models import Count, Q
        
        # Annotate com contagens por status
        summary_data = []
        
        # Busca todas as extraction_units que têm solicitações
        extraction_units = queryset.exclude(
            extraction_unit__isnull=True
        ).values_list('extraction_unit', flat=True).distinct()
        
        from apps.core.models import ExtractionUnit
        
        for unit_id in extraction_units:
            unit_requests = queryset.filter(extraction_unit_id=unit_id)
            unit = unit_requests.first().extraction_unit
            
            # Conta por status
            status_counts = {}
            for status_code, status_label in ExtractionRequest.REQUEST_STATUS_CHOICES:
                status_counts[status_code] = unit_requests.filter(status=status_code).count()
            
            # Total de solicitações
            total = unit_requests.count()
            
            # Solicitações não recebidas
            not_received = unit_requests.filter(
                received_at__isnull=True,
                status__in=[
                    ExtractionRequest.REQUEST_STATUS_PENDING,
                    ExtractionRequest.REQUEST_STATUS_ASSIGNED
                ]
            ).count()
            
            summary_data.append({
                'extraction_unit': unit,
                'total': total,
                'not_received': not_received,
                'status_counts': status_counts,
                'requests': unit_requests.order_by('-requested_at', '-created_at')[:10]  # Últimas 10
            })
        
        # Ordena por total (maior primeiro)
        summary_data.sort(key=lambda x: x['total'], reverse=True)
        
        # Solicitações sem extraction_unit
        requests_without_unit = queryset.filter(extraction_unit__isnull=True)
        if requests_without_unit.exists():
            status_counts_no_unit = {}
            for status_code, status_label in ExtractionRequest.REQUEST_STATUS_CHOICES:
                status_counts_no_unit[status_code] = requests_without_unit.filter(status=status_code).count()
            
            summary_data.append({
                'extraction_unit': None,
                'total': requests_without_unit.count(),
                'not_received': requests_without_unit.filter(
                    received_at__isnull=True,
                    status__in=[
                        ExtractionRequest.REQUEST_STATUS_PENDING,
                        ExtractionRequest.REQUEST_STATUS_ASSIGNED
                    ]
                ).count(),
                'status_counts': status_counts_no_unit,
                'requests': requests_without_unit.order_by('-requested_at', '-created_at')[:10]
            })
        
        context['summary_data'] = summary_data
        context['page_title'] = 'Distribuição por Unidade de Extração'
        context['page_icon'] = 'fa-chart-bar'
        context['form'] = ExtractionRequestSearchForm(self.request.GET or None)
        context['total_count'] = queryset.count()
        
        return context
