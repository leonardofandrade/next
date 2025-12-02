from django import forms
from django.utils.translation import gettext_lazy as _
from apps.base_tables.models import (
    Organization,
    Agency,
    Department,
    AgencyUnit,
    EmployeePosition,
    ProcedureCategory,
    CrimeCategory,
    DeviceCategory,
    DeviceBrand,
    DeviceModel
)


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'acronym', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da instituição'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
        }


class AgencyForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['organization', 'name', 'acronym', 'description']
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da agência'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].queryset = Organization.objects.filter(deleted_at__isnull=True)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['agency', 'name', 'acronym', 'description', 'parent_department']
        widgets = {
            'agency': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do departamento'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
            'parent_department': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agency'].queryset = Agency.objects.filter(deleted_at__isnull=True)
        self.fields['parent_department'].queryset = Department.objects.filter(deleted_at__isnull=True)
        self.fields['parent_department'].required = False


class AgencyUnitForm(forms.ModelForm):
    class Meta:
        model = AgencyUnit
        fields = [
            'agency', 'name', 'acronym', 'description',
            'phone_number', 'secondary_phone', 'primary_email',
            'address_line_1', 'address_number', 'address_line_2',
            'neighborhood', 'city', 'state', 'country', 'address_postal_code'
        ]
        widgets = {
            'agency': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da unidade'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(85) 99999-9999'}),
            'secondary_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(85) 99999-9999'}),
            'primary_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua, Avenida, etc.'}),
            'address_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Complemento'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Estado'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'País'}),
            'address_postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CEP'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agency'].queryset = Agency.objects.filter(deleted_at__isnull=True)
        self.fields['agency'].required = False


class EmployeePositionForm(forms.ModelForm):
    class Meta:
        model = EmployeePosition
        fields = ['name', 'acronym', 'description', 'default_selection']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do cargo'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
            'default_selection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProcedureCategoryForm(forms.ModelForm):
    class Meta:
        model = ProcedureCategory
        fields = ['name', 'acronym', 'description', 'default_selection']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da categoria'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
            'default_selection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CrimeCategoryForm(forms.ModelForm):
    class Meta:
        model = CrimeCategory
        fields = ['name', 'acronym', 'description', 'default_selection']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da categoria'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
            'default_selection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DeviceCategoryForm(forms.ModelForm):
    class Meta:
        model = DeviceCategory
        fields = ['name', 'acronym', 'description', 'default_selection']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da categoria'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
            'default_selection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DeviceBrandForm(forms.ModelForm):
    class Meta:
        model = DeviceBrand
        fields = ['name', 'acronym', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da marca'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
        }


class DeviceModelForm(forms.ModelForm):
    class Meta:
        model = DeviceModel
        fields = ['brand', 'name', 'commercial_name', 'code', 'description']
        widgets = {
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do modelo'}),
            'commercial_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome comercial'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['brand'].queryset = DeviceBrand.objects.filter(deleted_at__isnull=True)
