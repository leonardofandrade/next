"""
Custom managers and querysets for optimized database queries
"""
from django.db import models
from django.db.models import Q, Count, Prefetch, F, Case, When
from django.utils import timezone
from typing import Optional, List


class AuditedQuerySet(models.QuerySet):
    """Base queryset for audited models with common filters"""
    
    def active(self):
        """Filter only non-deleted records"""
        return self.filter(deleted_at__isnull=True)
    
    def deleted(self):
        """Filter only deleted records"""
        return self.filter(deleted_at__isnull=False)
    
    def created_by_user(self, user):
        """Filter records created by specific user"""
        return self.filter(created_by=user)
    
    def created_in_period(self, start_date, end_date):
        """Filter records created in specific period"""
        return self.filter(created_at__range=[start_date, end_date])
    
    def updated_since(self, date):
        """Filter records updated since date"""
        return self.filter(updated_at__gte=date)


class AuditedManager(models.Manager):
    """Base manager for audited models"""
    
    def get_queryset(self):
        return AuditedQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def deleted(self):
        return self.get_queryset().deleted()


class CaseQuerySet(AuditedQuerySet):
    """Custom queryset for Case model with optimized queries"""
    
    def with_related_data(self):
        """Prefetch all related data for optimal performance"""
        return self.select_related(
            'procedure_category',
            'requester_agency',
            'requester_department',
            'requester_agency_unit',
            'created_by'
        ).prefetch_related(
            'devices__device_category',
            'devices__device_model__brand',
            'extractions__assigned_to__user'
        )
    
    def by_status(self, status):
        """Filter by case status"""
        return self.filter(status=status)
    
    def by_year(self, year):
        """Filter by case year"""
        return self.filter(year=year)
    
    def by_procedure_category(self, category_id):
        """Filter by procedure category"""
        return self.filter(procedure_category_id=category_id)
    
    def search(self, query):
        """Search in case number, requester name or description"""
        if not query:
            return self
        return self.filter(
            Q(number__icontains=query) |
            Q(requester_name__icontains=query) |
            Q(description__icontains=query)
        )
    
    def pending_extractor(self):
        """Cases waiting for extractor assignment"""
        return self.filter(status='waiting_extractor')
    
    def in_progress(self):
        """Cases currently in progress"""
        return self.filter(status='in_progress')
    
    def completed(self):
        """Completed cases"""
        return self.filter(status='completed')
    
    def with_statistics(self):
        """Add extraction statistics to each case"""
        return self.annotate(
            total_devices=Count('devices', filter=Q(devices__deleted_at__isnull=True)),
            total_extractions=Count('extractions', filter=Q(extractions__deleted_at__isnull=True)),
            pending_extractions=Count(
                'extractions',
                filter=Q(
                    extractions__deleted_at__isnull=True,
                    extractions__status='pending'
                )
            ),
            completed_extractions=Count(
                'extractions',
                filter=Q(
                    extractions__deleted_at__isnull=True,
                    extractions__status='completed'  
                )
            )
        )


class CaseManager(AuditedManager):
    """Custom manager for Case model"""
    
    def get_queryset(self):
        return CaseQuerySet(self.model, using=self._db)
    
    def with_related_data(self):
        return self.get_queryset().with_related_data()
    
    def search(self, query):
        return self.get_queryset().search(query)
    
    def by_status(self, status):
        return self.get_queryset().by_status(status)
    
    def dashboard_summary(self):
        """Get cases summary for dashboard"""
        return self.active().aggregate(
            total=Count('id'),
            pending_extractor=Count('id', filter=Q(status='waiting_extractor')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed')),
            draft=Count('id', filter=Q(status='draft'))
        )


class ExtractionQuerySet(AuditedQuerySet):
    """Custom queryset for Extraction model"""
    
    def with_related_data(self):
        """Prefetch all related data for optimal performance"""
        return self.select_related(
            'case_device__case',
            'case_device__device_category', 
            'case_device__device_model__brand',
            'assigned_to__user',
            'assigned_by',
            'started_by__user',
            'finished_by__user',
            'storage_media'
        )
    
    def by_status(self, status):
        """Filter by extraction status"""
        return self.filter(status=status)
    
    def by_case(self, case):
        """Filter by case"""
        return self.filter(case_device__case=case)
    
    def assigned_to_user(self, extractor_user):
        """Filter extractions assigned to specific user"""
        return self.filter(assigned_to=extractor_user)
    
    def pending(self):
        """Pending extractions"""
        return self.filter(status='pending')
    
    def assigned(self):
        """Assigned extractions"""
        return self.filter(status='assigned')
    
    def in_progress(self):
        """In progress extractions"""
        return self.filter(status='in_progress')
    
    def completed(self):
        """Completed extractions"""
        return self.filter(status='completed')
    
    def paused(self):
        """Paused extractions"""
        return self.filter(status='paused')
    
    def search(self, query):
        """Search in device model, IMEI, owner name or case number"""
        if not query:
            return self
        return self.filter(
            Q(case_device__device_model__name__icontains=query) |
            Q(case_device__imei__icontains=query) |  
            Q(case_device__owner_name__icontains=query) |
            Q(case_device__case__number__icontains=query)
        )
    
    def overdue(self, days=30):
        """Extractions overdue by specified days"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(
            created_at__lt=cutoff_date,
            status__in=['pending', 'assigned', 'in_progress']
        )


class ExtractionManager(AuditedManager):
    """Custom manager for Extraction model"""
    
    def get_queryset(self):
        return ExtractionQuerySet(self.model, using=self._db)
    
    def with_related_data(self):
        return self.get_queryset().with_related_data()
    
    def by_status(self, status):
        return self.get_queryset().by_status(status)
    
    def dashboard_summary(self):
        """Get extraction summary for dashboard"""
        return self.active().aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            assigned=Count('id', filter=Q(status='assigned')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed')),
            paused=Count('id', filter=Q(status='paused'))
        )
    
    def workload_by_extractor(self):
        """Get workload statistics by extractor"""
        return self.active().filter(
            assigned_to__isnull=False
        ).values(
            'assigned_to__user__username',
            'assigned_to__user__first_name',
            'assigned_to__user__last_name'
        ).annotate(
            total_assigned=Count('id'),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed')),
            pending_start=Count('id', filter=Q(status='assigned'))
        ).order_by('-total_assigned')


class BaseTableQuerySet(AuditedQuerySet):
    """Base queryset for lookup tables"""
    
    def by_name(self, name):
        """Filter by name (case insensitive)"""
        return self.filter(name__icontains=name)
    
    def by_acronym(self, acronym):
        """Filter by acronym"""
        return self.filter(acronym__iexact=acronym)
    
    def search(self, query):
        """Search in name, acronym or description"""
        if not query:
            return self
        return self.filter(
            Q(name__icontains=query) |
            Q(acronym__icontains=query) |
            Q(description__icontains=query)
        )


class BaseTableManager(AuditedManager):
    """Manager for lookup tables"""
    
    def get_queryset(self):
        return BaseTableQuerySet(self.model, using=self._db)
    
    def search(self, query):
        return self.get_queryset().search(query)
    
    def ordered(self):
        """Get records ordered by name"""
        return self.active().order_by('name')


class DeviceModelQuerySet(AuditedQuerySet):
    """Custom queryset for DeviceModel"""
    
    def with_brand(self):
        """Include brand information"""
        return self.select_related('brand')
    
    def by_brand(self, brand_id):
        """Filter by brand"""
        return self.filter(brand_id=brand_id)
    
    def search(self, query):
        """Search in model name, commercial name or brand"""
        if not query:
            return self
        return self.filter(
            Q(name__icontains=query) |
            Q(commercial_name__icontains=query) |
            Q(brand__name__icontains=query)
        )


class DeviceModelManager(AuditedManager):
    """Manager for DeviceModel"""
    
    def get_queryset(self):
        return DeviceModelQuerySet(self.model, using=self._db)
    
    def with_brand(self):
        return self.get_queryset().with_brand()
    
    def search(self, query):
        return self.get_queryset().search(query)
    
    def by_brand(self, brand_id):
        return self.get_queryset().by_brand(brand_id)