"""
Views para o app extractions
"""
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, View
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from apps.cases.models import Case, Extraction
from apps.extractions.forms import ExtractionSearchForm
from apps.core.models import ExtractorUser


class ExtractionListView(LoginRequiredMixin, ListView):
    """
    Lista todas as extrações com filtros de busca
    """
    model = Extraction
    template_name = 'extractions/extraction_list.html'
    context_object_name = 'page_obj'
    paginate_by = 25
    
    def get_queryset(self):
        """
        Retorna o queryset filtrado com base nos parâmetros de busca
        """
        queryset = Extraction.objects.filter(
            deleted_at__isnull=True,
            case_device__deleted_at__isnull=True,
            case_device__case__deleted_at__isnull=True
        ).select_related(
            'case_device__device_category',
            'case_device__device_model__brand',
            'case_device__case',
            'assigned_to__user',
            'assigned_by',
            'started_by__user',
            'finished_by__user',
            'storage_media'
        ).order_by('-created_at')
        
        form = ExtractionSearchForm(self.request.GET or None)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                # Busca por modelo, IMEI ou proprietário
                queryset = queryset.filter(
                    Q(case_device__device_model__name__icontains=search) |
                    Q(case_device__device_model__brand__name__icontains=search) |
                    Q(case_device__imei_01__icontains=search) |
                    Q(case_device__imei_02__icontains=search) |
                    Q(case_device__imei_03__icontains=search) |
                    Q(case_device__imei_04__icontains=search) |
                    Q(case_device__imei_05__icontains=search) |
                    Q(case_device__owner_name__icontains=search)
                )
            
            case_number = form.cleaned_data.get('case_number')
            if case_number:
                queryset = queryset.filter(
                    case_device__case__number__icontains=case_number
                )
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            extraction_unit = form.cleaned_data.get('extraction_unit')
            if extraction_unit:
                queryset = queryset.filter(
                    case_device__case__extraction_unit=extraction_unit
                )
            
            assigned_to = form.cleaned_data.get('assigned_to')
            if assigned_to:
                # assigned_to é um User, mas precisamos filtrar por ExtractorUser
                queryset = queryset.filter(assigned_to__user=assigned_to)
            
            extraction_result = form.cleaned_data.get('extraction_result')
            if extraction_result:
                queryset = queryset.filter(extraction_result=extraction_result)
            
            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            
            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Adiciona o formulário de busca e total_count ao contexto
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Extrações'
        context['page_icon'] = 'fa-database'
        context['form'] = ExtractionSearchForm(self.request.GET or None)
        context['total_count'] = self.get_queryset().count()
        return context


class CaseExtractionsView(LoginRequiredMixin, DetailView):
    """
    Exibe as extrações de um processo de extração
    """
    model = Case
    template_name = 'extractions/case_extractions.html'
    context_object_name = 'case'
    
    def get_queryset(self):
        """
        Filtra apenas casos não deletados
        """
        return Case.objects.filter(deleted_at__isnull=True)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona as extrações do caso ao contexto
        """
        context = super().get_context_data(**kwargs)
        case = self.get_object()
        
        # Busca extrações através dos dispositivos do caso
        # Filtra apenas dispositivos não deletados e suas extrações
        extractions = Extraction.objects.filter(
            case_device__case=case,
            case_device__deleted_at__isnull=True,
            deleted_at__isnull=True
        ).select_related(
            'case_device__device_category',
            'case_device__device_model__brand',
            'assigned_to',
            'assigned_by',
            'started_by',
            'finished_by',
            'storage_media'
        ).order_by('-created_at')
        
        # Verifica se há dispositivos sem extração
        devices_without_extraction = case.case_devices.filter(
            deleted_at__isnull=True
        ).exclude(
            pk__in=Extraction.objects.values_list('case_device_id', flat=True)
        ).exists()
        
        context['page_title'] = f'Extrações - Processo {case.number if case.number else f"#{case.pk}"}'
        context['page_icon'] = 'fa-database'
        context['extractions'] = extractions
        context['has_devices_without_extractions'] = devices_without_extraction
        return context


class ExtractionAssignToMeView(LoginRequiredMixin, View):
    """
    Atribui a extração ao usuário extrator logado
    """
    
    def post(self, request, pk):
        """
        Atribui a extração ao usuário extrator logado
        """
        extraction = get_object_or_404(
            Extraction.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o usuário é um extrator
        try:
            extractor_user = ExtractorUser.objects.get(
                user=request.user,
                deleted_at__isnull=True
            )
        except ExtractorUser.DoesNotExist:
            messages.error(
                request,
                'Você não é um usuário extrator. Apenas extratores podem se atribuir a extrações.'
            )
            return self._redirect_back(request, extraction)
        
        # Verifica se a extração já está atribuída ao usuário
        if extraction.assigned_to == extractor_user:
            messages.warning(
                request,
                'Esta extração já está atribuída a você.'
            )
        else:
            # Atribui a extração ao usuário
            extraction.assigned_to = extractor_user
            extraction.assigned_at = timezone.now()
            extraction.assigned_by = request.user
            
            # Atualiza o status se estiver pending
            if extraction.status == Extraction.STATUS_PENDING:
                extraction.status = Extraction.STATUS_ASSIGNED
            
            extraction.save()
            
            messages.success(
                request,
                f'Extração atribuída a você com sucesso!'
            )
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """
        Redireciona de acordo com o referer ou para as extrações do caso
        """
        referer = request.META.get('HTTP_REFERER')
        if referer and 'extractions/list' in referer:
            return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionUnassignFromMeView(LoginRequiredMixin, View):
    """
    Remove a atribuição da extração do usuário extrator logado
    """
    
    def post(self, request, pk):
        """
        Remove a atribuição da extração do usuário extrator logado
        """
        extraction = get_object_or_404(
            Extraction.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o usuário é um extrator
        try:
            extractor_user = ExtractorUser.objects.get(
                user=request.user,
                deleted_at__isnull=True
            )
        except ExtractorUser.DoesNotExist:
            messages.error(
                request,
                'Você não é um usuário extrator.'
            )
            return self._redirect_back(request, extraction)
        
        # Verifica se a extração está atribuída ao usuário (apenas o responsável pode se desatribuir)
        if extraction.assigned_to != extractor_user:
            messages.error(
                request,
                'Você não tem permissão para desatribuir esta extração. Apenas o responsável pode se desatribuir.'
            )
        else:
            # Verifica se a extração já foi iniciada
            if extraction.status in [Extraction.STATUS_IN_PROGRESS, Extraction.STATUS_COMPLETED]:
                messages.error(
                    request,
                    'Não é possível desatribuir uma extração que já foi iniciada ou finalizada.'
                )
            else:
                # Remove a atribuição
                extraction.assigned_to = None
                extraction.assigned_at = None
                extraction.assigned_by = None
                
                # Volta o status para pending se estiver assigned
                if extraction.status == Extraction.STATUS_ASSIGNED:
                    extraction.status = Extraction.STATUS_PENDING
                
                extraction.save()
                
                messages.success(
                    request,
                    'Atribuição removida com sucesso!'
                )
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """
        Redireciona de acordo com o referer ou para as extrações do caso
        """
        referer = request.META.get('HTTP_REFERER')
        if referer and 'extractions/list' in referer:
            return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)


class ExtractionStartView(LoginRequiredMixin, View):
    """
    Inicia uma extração, atribuindo ao usuário se necessário
    """
    
    def post(self, request, pk):
        """
        Inicia a extração, fazendo atribuição automática se necessário
        """
        extraction = get_object_or_404(
            Extraction.objects.filter(deleted_at__isnull=True),
            pk=pk
        )
        
        # Verifica se o usuário é um extrator
        try:
            extractor_user = ExtractorUser.objects.get(
                user=request.user,
                deleted_at__isnull=True
            )
        except ExtractorUser.DoesNotExist:
            messages.error(
                request,
                'Você não é um usuário extrator. Apenas extratores podem iniciar extrações.'
            )
            return self._redirect_back(request, extraction)
        
        # Verifica se a extração já está em andamento ou finalizada
        if extraction.status == Extraction.STATUS_IN_PROGRESS:
            messages.warning(
                request,
                'Esta extração já está em andamento.'
            )
            return self._redirect_back(request, extraction)
        
        if extraction.status == Extraction.STATUS_COMPLETED:
            messages.error(
                request,
                'Esta extração já foi finalizada e não pode ser iniciada novamente.'
            )
            return self._redirect_back(request, extraction)
        
        # Se não estiver atribuída, atribui automaticamente ao usuário
        if not extraction.assigned_to:
            extraction.assigned_to = extractor_user
            extraction.assigned_at = timezone.now()
            extraction.assigned_by = request.user
            messages.info(
                request,
                'Extração atribuída automaticamente a você.'
            )
        else:
            # Verifica se está atribuída a outro usuário
            if extraction.assigned_to != extractor_user:
                messages.error(
                    request,
                    f'Esta extração está atribuída a {extraction.assigned_to.user.get_full_name() or extraction.assigned_to.user.username}. '
                    'Apenas o responsável pode iniciá-la.'
                )
                return self._redirect_back(request, extraction)
        
        # Inicia a extração
        extraction.status = Extraction.STATUS_IN_PROGRESS
        extraction.started_at = timezone.now()
        extraction.started_by = extractor_user
        
        # Obtém as notas do formulário se fornecidas
        notes = request.POST.get('notes', '')
        if notes:
            extraction.started_notes = notes
        
        extraction.save()
        
        messages.success(
            request,
            'Extração iniciada com sucesso!'
        )
        
        return self._redirect_back(request, extraction)
    
    def _redirect_back(self, request, extraction):
        """
        Redireciona de acordo com o referer ou para as extrações do caso
        """
        referer = request.META.get('HTTP_REFERER')
        if referer and 'extractions/list' in referer:
            return redirect('extractions:list')
        return redirect('extractions:case_extractions', pk=extraction.case_device.case.pk)
