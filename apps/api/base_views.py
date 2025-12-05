"""
Base API views using Django REST Framework
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any

from apps.core.services.base import BaseService, ServiceException


class BaseAPIViewSet(ModelViewSet):
    """
    Base ViewSet for API endpoints using service layer
    
    This provides standard CRUD operations using the service layer,
    ensuring consistency between web views and API endpoints.
    """
    
    service_class = None
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_service(self) -> BaseService:
        """Get service instance with current user"""
        if self.service_class is None:
            raise NotImplementedError("service_class must be defined")
        return self.service_class(user=self.request.user)
    
    def handle_service_exception(self, exception: ServiceException) -> Response:
        """Handle service exceptions and return appropriate response"""
        return Response(
            {'detail': str(exception)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def get_queryset(self):
        """Get queryset using service"""
        service = self.get_service()
        filters = self.get_filters()
        
        try:
            return service.list_filtered(filters)
        except ServiceException as e:
            # Return empty queryset on error  
            return self.queryset.none() if hasattr(self, 'queryset') else []
    
    def get_filters(self) -> Dict[str, Any]:
        """Extract filters from query parameters"""
        filters = {}
        
        # Common filters
        if search := self.request.query_params.get('search'):
            filters['search'] = search
            
        if status_param := self.request.query_params.get('status'):
            filters['status'] = status_param
            
        return filters
    
    def create(self, request, *args, **kwargs):
        """Create object using service"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        
        try:
            instance = service.create(serializer.validated_data)
            output_serializer = self.get_serializer(instance)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except ServiceException as e:
            return self.handle_service_exception(e)
    
    def update(self, request, *args, **kwargs):
        """Update object using service"""
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        
        try:
            instance = service.update(kwargs['pk'], serializer.validated_data)
            output_serializer = self.get_serializer(instance)
            return Response(output_serializer.data)
        except ServiceException as e:
            return self.handle_service_exception(e)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete object using service"""
        service = self.get_service()
        
        try:
            service.delete(kwargs['pk'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ServiceException as e:
            return self.handle_service_exception(e)


class ReadOnlyAPIViewSet(BaseAPIViewSet):
    """Read-only API ViewSet for lookup tables"""
    
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAuthenticated]  # Less restrictive for read-only
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search endpoint"""
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        
        filters = {'search': query}
        service = self.get_service()
        
        try:
            queryset = service.list_filtered(filters)[:20]  # Limit results
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except ServiceException as e:
            return self.handle_service_exception(e)