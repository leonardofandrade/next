"""
Serializers for API endpoints
"""
from rest_framework import serializers
from apps.cases.models import Case, CaseDevice, Extraction
from apps.base_tables.models import (
    Organization, Agency, Department, AgencyUnit,
    ProcedureCategory, CrimeCategory, DeviceCategory,
    DeviceBrand, DeviceModel
)


class BaseAuditedSerializer(serializers.ModelSerializer):
    """Base serializer for audited models"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        fields = [
            'id', 'created_at', 'updated_at', 
            'created_by', 'created_by_name',
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]


class ProcedureCategorySerializer(BaseAuditedSerializer):
    """Serializer for ProcedureCategory"""
    
    class Meta(BaseAuditedSerializer.Meta):
        model = ProcedureCategory
        fields = BaseAuditedSerializer.Meta.fields + [
            'name', 'acronym', 'description'
        ]


class DeviceCategorySerializer(BaseAuditedSerializer):
    """Serializer for DeviceCategory"""
    
    class Meta(BaseAuditedSerializer.Meta):
        model = DeviceCategory
        fields = BaseAuditedSerializer.Meta.fields + [
            'name', 'acronym', 'description'
        ]


class DeviceBrandSerializer(BaseAuditedSerializer):
    """Serializer for DeviceBrand"""
    
    class Meta(BaseAuditedSerializer.Meta):
        model = DeviceBrand
        fields = BaseAuditedSerializer.Meta.fields + [
            'name', 'acronym', 'description'
        ]


class DeviceModelSerializer(BaseAuditedSerializer):
    """Serializer for DeviceModel"""
    
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta(BaseAuditedSerializer.Meta):
        model = DeviceModel
        fields = BaseAuditedSerializer.Meta.fields + [
            'brand', 'brand_name', 'name', 'commercial_name', 'code'
        ]


class CaseDeviceSerializer(BaseAuditedSerializer):
    """Serializer for CaseDevice"""
    
    device_category_name = serializers.CharField(source='device_category.name', read_only=True)
    device_model_name = serializers.CharField(source='device_model.name', read_only=True)
    device_brand_name = serializers.CharField(source='device_model.brand.name', read_only=True)
    
    class Meta(BaseAuditedSerializer.Meta):
        model = CaseDevice
        fields = BaseAuditedSerializer.Meta.fields + [
            'case', 'device_category', 'device_category_name',
            'device_model', 'device_model_name', 'device_brand_name',
            'imei', 'owner_name', 'owner_document',
            'device_password', 'device_pattern', 'observations'
        ]


class CaseListSerializer(BaseAuditedSerializer):
    """Lightweight serializer for Case listing"""
    
    procedure_category_name = serializers.CharField(source='procedure_category.name', read_only=True)
    requester_agency_name = serializers.CharField(source='requester_agency.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta(BaseAuditedSerializer.Meta):
        model = Case
        fields = BaseAuditedSerializer.Meta.fields + [
            'number', 'year', 'status', 'status_display',
            'procedure_category', 'procedure_category_name',
            'requester_agency', 'requester_agency_name',
            'requester_name', 'description'
        ]


class CaseDetailSerializer(CaseListSerializer):
    """Detailed serializer for Case with related data"""
    
    devices = CaseDeviceSerializer(many=True, read_only=True)
    total_devices = serializers.IntegerField(read_only=True)
    total_extractions = serializers.IntegerField(read_only=True)
    
    class Meta(CaseListSerializer.Meta):
        fields = CaseListSerializer.Meta.fields + [
            'devices', 'total_devices', 'total_extractions',
            'requester_department', 'requester_agency_unit',
            'requester_email', 'requester_phone',
            'priority', 'deadline_date', 'observations'
        ]


class ExtractionSerializer(BaseAuditedSerializer):
    """Serializer for Extraction"""
    
    case_number = serializers.CharField(source='case_device.case.number', read_only=True)
    device_model_name = serializers.CharField(source='case_device.device_model.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta(BaseAuditedSerializer.Meta):
        model = Extraction
        fields = BaseAuditedSerializer.Meta.fields + [
            'case_device', 'case_number', 'device_model_name',
            'status', 'status_display',
            'assigned_to', 'assigned_to_name',
            'started_at', 'finished_at',
            'storage_media', 'observations'
        ]