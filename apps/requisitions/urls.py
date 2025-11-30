from django.urls import path
from apps.requisitions.views import (
    ExtractionRequestListView,
    ExtractionRequestDetailView,
    ExtractionRequestCreateView,
    ExtractionRequestUpdateView,
    ExtractionRequestDeleteView,
    ExtractionRequestNotReceivedView,
    CreateCaseFromRequestView,
)

app_name = 'requisitions'

urlpatterns = [
    path('', ExtractionRequestListView.as_view(), name='list'),
    path('not-received/', ExtractionRequestNotReceivedView.as_view(), name='not_received'),
    path('<int:pk>/', ExtractionRequestDetailView.as_view(), name='detail'),
    path('create/', ExtractionRequestCreateView.as_view(), name='create'),
    path('<int:pk>/update/', ExtractionRequestUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', ExtractionRequestDeleteView.as_view(), name='delete'),
    path('<int:pk>/create-case/', CreateCaseFromRequestView.as_view(), name='create_case'),
]