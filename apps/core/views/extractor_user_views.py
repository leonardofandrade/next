"""
Views de gerenciamento de usuários extratores (ExtractorUser) e permissões por ExtractionUnit.

Escopo: ExtractionAgency (singleton).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import FormView

from apps.core.forms import ExtractorUserAccessForm
from apps.core.models import ExtractionAgency, ExtractorUser, ExtractionUnitExtractor, ExtractionUnit


class ExtractorUserCreateView(LoginRequiredMixin, FormView):
    template_name = 'core/extractor_user_access_form.html'
    form_class = ExtractorUserAccessForm

    def dispatch(self, request, *args, **kwargs):
        self.agency = ExtractionAgency.objects.first()
        if not self.agency:
            # garante que o hub funcione mesmo sem dados carregados
            self.agency = ExtractionAgency.objects.create(acronym='', name='')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['extraction_agency'] = self.agency
        kwargs['extractor_user'] = None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency'] = self.agency
        context['page_title'] = _('Adicionar usuário extrator')
        context['page_description'] = _('Selecione um usuário existente e defina quais unidades ele pode acessar.')
        return context

    def form_valid(self, form):
        user = form.cleaned_data['user']
        selected_units = list(form.cleaned_data.get('extraction_units') or [])

        with transaction.atomic():
            extractor_user = ExtractorUser.objects.filter(
                user=user,
                extraction_agency=self.agency,
            ).first()

            if extractor_user:
                # reativa se estava "removido"
                if extractor_user.deleted_at is not None:
                    extractor_user.deleted_at = None
                    extractor_user.deleted_by = None
                    extractor_user.save()
            else:
                extractor_user = ExtractorUser.objects.create(
                    user=user,
                    extraction_agency=self.agency,
                )

            self._sync_extractor_units(extractor_user, selected_units)
            # Armazena para usar no get_success_url
            self.extractor_user = extractor_user

        messages.success(self.request, _('Usuário extrator configurado com sucesso!'))
        return super().form_valid(form)

    def _sync_extractor_units(self, extractor_user: ExtractorUser, selected_units: list[ExtractionUnit]):
        selected_ids = {u.pk for u in selected_units}

        # só permite unidades da própria agência (segurança)
        allowed_units = set(
            ExtractionUnit.objects.filter(agency=self.agency, deleted_at__isnull=True).values_list('pk', flat=True)
        )
        selected_ids = selected_ids.intersection(allowed_units)

        existing_links = list(
            ExtractionUnitExtractor.objects.filter(
                extractor=extractor_user,
                extraction_unit__agency=self.agency,
            )
        )
        by_unit_id = {link.extraction_unit_id: link for link in existing_links}

        now = timezone.now()

        # ativa/cria os selecionados
        for unit_id in selected_ids:
            link = by_unit_id.get(unit_id)
            if link:
                if link.deleted_at is not None:
                    link.deleted_at = None
                    link.deleted_by = None
                    link.save()
            else:
                ExtractionUnitExtractor.objects.create(
                    extractor=extractor_user,
                    extraction_unit_id=unit_id,
                )

        # remove (soft delete) os não selecionados
        for link in existing_links:
            if link.extraction_unit_id not in selected_ids and link.deleted_at is None:
                link.deleted_at = now
                link.deleted_by = self.request.user
                link.save()

    def get_success_url(self):
        # Após criar, redireciona para a página de edição
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        # Redireciona para a página de edição do extrator criado
        return reverse('core:extractor_user_update', kwargs={'pk': self.extractor_user.pk})


class ExtractorUserUpdateView(LoginRequiredMixin, FormView):
    template_name = 'core/extractor_user_access_form.html'
    form_class = ExtractorUserAccessForm

    def dispatch(self, request, *args, **kwargs):
        self.agency = ExtractionAgency.objects.first()
        if not self.agency:
            raise Http404('Agência de extração não encontrada.')

        try:
            self.extractor_user = ExtractorUser.objects.select_related('user').get(pk=self.kwargs['pk'])
        except ExtractorUser.DoesNotExist as exc:
            raise Http404('Usuário extrator não encontrado.') from exc

        if self.extractor_user.extraction_agency_id != self.agency.pk:
            raise Http404('Usuário extrator não pertence à agência atual.')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['extraction_agency'] = self.agency
        kwargs['extractor_user'] = self.extractor_user
        return kwargs

    def get_initial(self):
        # evita depender de initial no form quando user estiver disabled
        return {'user': self.extractor_user.user_id}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agency'] = self.agency
        context['extractor_user'] = self.extractor_user
        context['page_title'] = _('Editar usuário extrator')
        context['page_description'] = _('Defina quais unidades este extrator pode acessar.')
        return context

    def form_valid(self, form):
        selected_units = list(form.cleaned_data.get('extraction_units') or [])
        with transaction.atomic():
            # garante ativo
            if self.extractor_user.deleted_at is not None:
                self.extractor_user.deleted_at = None
                self.extractor_user.deleted_by = None
                self.extractor_user.save()

            ExtractorUserCreateView._sync_extractor_units(self, self.extractor_user, selected_units)  # reuse

        messages.success(self.request, _('Permissões do extrator atualizadas com sucesso!'))
        return super().form_valid(form)

    def get_success_url(self):
        # Mantém na mesma página após salvar
        next_url = self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        # Redireciona para a própria página de edição
        return reverse('core:extractor_user_update', kwargs={'pk': self.extractor_user.pk})


class ExtractorUserUnitsAjaxView(LoginRequiredMixin, View):
    """
    Endpoint AJAX que retorna as unidades associadas a um usuário para a agência atual.
    """

    def get(self, request):
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'user_id é obrigatório'}, status=400)

        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Usuário não encontrado'}, status=404)

        agency = ExtractionAgency.objects.first()
        if not agency:
            return JsonResponse({'unit_ids': []})

        # Busca o ExtractorUser do usuário para esta agência
        extractor_user = ExtractorUser.objects.filter(
            user=user,
            extraction_agency=agency,
            deleted_at__isnull=True,
        ).first()

        if not extractor_user:
            return JsonResponse({'unit_ids': []})

        # Retorna os IDs das unidades ativas associadas
        unit_ids = list(
            ExtractionUnitExtractor.objects.filter(
                extractor=extractor_user,
                extraction_unit__agency=agency,
                deleted_at__isnull=True,
                extraction_unit__deleted_at__isnull=True,
            ).values_list('extraction_unit_id', flat=True)
        )

        return JsonResponse({'unit_ids': unit_ids})

