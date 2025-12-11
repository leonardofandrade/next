from django.urls import path
from apps.extractions import views
from apps.users.views.extractor_views import MyExtractionsView

app_name = 'extractions'


urlpatterns = [
    path('', views.ExtractionListView.as_view(), name='list'),
    path('case/<int:pk>/', views.CaseExtractionsView.as_view(), name='case_extractions'),
    path('<int:pk>/assign-to-me/', views.ExtractionAssignToMeView.as_view(), name='assign_to_me'),
    path('<int:pk>/unassign-from-me/', views.ExtractionUnassignFromMeView.as_view(), name='unassign_from_me'),
    path('<int:pk>/start/', views.ExtractionStartView.as_view(), name='start'),
    path('<int:pk>/pause/', views.ExtractionPauseView.as_view(), name='pause'),
    path('<int:pk>/resume/', views.ExtractionResumeView.as_view(), name='resume'),
    path('<int:pk>/finish-form/', views.ExtractionFinishFormView.as_view(), name='finish_form'),
    path('<int:pk>/finish-form-modal/', views.ExtractionFinishFormModalView.as_view(), name='finish_form_modal'),
    path('<int:pk>/finish/', views.ExtractionFinishView.as_view(), name='finish'),
    path('<int:pk>/brute-force/start/', views.BruteForceStartView.as_view(), name='brute_force_start'),
    path('<int:pk>/brute-force/finish-form-modal/', views.BruteForceFinishFormModalView.as_view(), name='brute_force_finish_form_modal'),
    path('<int:pk>/brute-force/finish/', views.BruteForceFinishView.as_view(), name='brute_force_finish'),
]