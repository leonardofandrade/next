"""
Exemplo de como refatorar as views existentes usando a nova arquitetura
"""
from apps.core.mixins.views import (
    BaseListView, BaseDetailView, BaseCreateView, 
    BaseUpdateView, BaseDeleteView
)
from apps.cases.services import CaseService, ExtractionService
from apps.cases.models import Case, Extraction
from apps.cases.forms import CaseForm, CaseSearchForm


class CaseListView(BaseListView):
    """
    Lista de casos usando a nova arquitetura baseada em services
    
    Antes: 50+ linhas de código duplicado
    Depois: 5 linhas de configuração
    """
    
    model = Case
    service_class = CaseService
    search_form_class = CaseSearchForm
    template_name = 'cases/case_list.html'
    context_object_name = 'cases'


class CaseDetailView(BaseDetailView):
    """Detalhes do caso"""
    
    model = Case  
    service_class = CaseService
    template_name = 'cases/case_detail.html'
    context_object_name = 'case'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.get_service()
        context['statistics'] = service.get_case_statistics(self.object)
        return context


class CaseCreateView(BaseCreateView):
    """Criação de caso"""
    
    model = Case
    service_class = CaseService
    form_class = CaseForm
    template_name = 'cases/case_form.html'


class CaseUpdateView(BaseUpdateView):
    """Atualização de caso"""
    
    model = Case
    service_class = CaseService  
    form_class = CaseForm
    template_name = 'cases/case_form.html'


class CaseDeleteView(BaseDeleteView):
    """Exclusão de caso"""
    
    model = Case
    service_class = CaseService
    template_name = 'cases/case_confirm_delete.html'


# Exemplo de view customizada usando service
class CaseCompleteRegistrationView(LoginRequiredMixin, View):
    """Finalizar cadastro do caso"""
    
    def post(self, request, pk):
        service = CaseService(user=request.user)
        create_extractions = request.POST.get('create_extractions') == 'on'
        
        try:
            case = service.complete_registration(pk, create_extractions)
            messages.success(request, 'Cadastro finalizado com sucesso!')
            return redirect('cases:detail', pk=case.pk)
        except ServiceException as e:
            messages.error(request, str(e))
            return redirect('cases:detail', pk=pk)


# Views de extração usando services
class ExtractionAssignToMeView(LoginRequiredMixin, View):
    """Atribuir extração ao usuário atual"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        try:
            # Assumindo que existe lógica para obter ExtractorUser do User
            extractor_user = request.user.extractor_profile  
            extraction = service.assign_extraction(pk, extractor_user.pk)
            
            messages.success(request, 'Extração atribuída com sucesso!')
            return JsonResponse({'success': True})
        except ServiceException as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ExtractionStartView(LoginRequiredMixin, View):
    """Iniciar extração"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        try:
            extraction = service.start_extraction(pk)
            messages.success(request, 'Extração iniciada com sucesso!')
            return JsonResponse({'success': True})
        except ServiceException as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ExtractionCompleteView(LoginRequiredMixin, View):
    """Finalizar extração"""
    
    def post(self, request, pk):
        service = ExtractionService(user=request.user)
        
        # Dados opcionais do formulário
        completion_data = {
            'observations': request.POST.get('observations', ''),
            'storage_media_id': request.POST.get('storage_media'),
            # outros campos...
        }
        
        try:
            extraction = service.complete_extraction(pk, **completion_data)
            messages.success(request, 'Extração finalizada com sucesso!')
            return JsonResponse({'success': True})
        except ServiceException as e:
            return JsonResponse({'success': False, 'error': str(e)})