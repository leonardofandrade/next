from django.urls import path
from . import views

app_name = 'base_tables'

urlpatterns = [
    # Organization URLs
    path('organizations/', views.OrganizationListView.as_view(), name='organization_list'),
    path('organizations/create/', views.OrganizationCreateView.as_view(), name='organization_create'),
    path('organizations/<int:pk>/edit/', views.OrganizationUpdateView.as_view(), name='organization_edit'),
    path('organizations/<int:pk>/delete/', views.OrganizationDeleteView.as_view(), name='organization_delete'),
    
    # Agency URLs
    path('agencies/', views.AgencyListView.as_view(), name='agency_list'),
    path('agencies/create/', views.AgencyCreateView.as_view(), name='agency_create'),
    path('agencies/<int:pk>/edit/', views.AgencyUpdateView.as_view(), name='agency_edit'),
    path('agencies/<int:pk>/delete/', views.AgencyDeleteView.as_view(), name='agency_delete'),
    
    # Department URLs
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    
    # AgencyUnit URLs
    path('agency-units/', views.AgencyUnitListView.as_view(), name='agency_unit_list'),
    path('agency-units/create/', views.AgencyUnitCreateView.as_view(), name='agency_unit_create'),
    path('agency-units/<int:pk>/edit/', views.AgencyUnitUpdateView.as_view(), name='agency_unit_edit'),
    path('agency-units/<int:pk>/delete/', views.AgencyUnitDeleteView.as_view(), name='agency_unit_delete'),
    
    # EmployeePosition URLs
    path('employee-positions/', views.EmployeePositionListView.as_view(), name='employee_position_list'),
    path('employee-positions/create/', views.EmployeePositionCreateView.as_view(), name='employee_position_create'),
    path('employee-positions/<int:pk>/edit/', views.EmployeePositionUpdateView.as_view(), name='employee_position_edit'),
    path('employee-positions/<int:pk>/delete/', views.EmployeePositionDeleteView.as_view(), name='employee_position_delete'),
    
    # ProcedureCategory URLs
    path('procedure-categories/', views.ProcedureCategoryListView.as_view(), name='procedure_category_list'),
    path('procedure-categories/create/', views.ProcedureCategoryCreateView.as_view(), name='procedure_category_create'),
    path('procedure-categories/<int:pk>/edit/', views.ProcedureCategoryUpdateView.as_view(), name='procedure_category_edit'),
    path('procedure-categories/<int:pk>/delete/', views.ProcedureCategoryDeleteView.as_view(), name='procedure_category_delete'),
    
    # CrimeCategory URLs
    path('crime-categories/', views.CrimeCategoryListView.as_view(), name='crime_category_list'),
    path('crime-categories/create/', views.CrimeCategoryCreateView.as_view(), name='crime_category_create'),
    path('crime-categories/<int:pk>/edit/', views.CrimeCategoryUpdateView.as_view(), name='crime_category_edit'),
    path('crime-categories/<int:pk>/delete/', views.CrimeCategoryDeleteView.as_view(), name='crime_category_delete'),
    
    # DeviceCategory URLs
    path('device-categories/', views.DeviceCategoryListView.as_view(), name='device_category_list'),
    path('device-categories/create/', views.DeviceCategoryCreateView.as_view(), name='device_category_create'),
    path('device-categories/<int:pk>/edit/', views.DeviceCategoryUpdateView.as_view(), name='device_category_edit'),
    path('device-categories/<int:pk>/delete/', views.DeviceCategoryDeleteView.as_view(), name='device_category_delete'),
    
    # DeviceBrand URLs
    path('device-brands/', views.DeviceBrandListView.as_view(), name='device_brand_list'),
    path('device-brands/create/', views.DeviceBrandCreateView.as_view(), name='device_brand_create'),
    path('device-brands/create-ajax/', views.DeviceBrandCreateAjaxView.as_view(), name='device_brand_create_ajax'),
    path('device-brands/<int:pk>/edit/', views.DeviceBrandUpdateView.as_view(), name='device_brand_edit'),
    path('device-brands/<int:pk>/delete/', views.DeviceBrandDeleteView.as_view(), name='device_brand_delete'),
    
    # DeviceModel URLs
    path('device-models/', views.DeviceModelListView.as_view(), name='device_model_list'),
    path('device-models/create/', views.DeviceModelCreateView.as_view(), name='device_model_create'),
    path('device-models/create-ajax/', views.DeviceModelCreateAjaxView.as_view(), name='device_model_create_ajax'),
    path('device-models/<int:pk>/edit/', views.DeviceModelUpdateView.as_view(), name='device_model_edit'),
    path('device-models/<int:pk>/delete/', views.DeviceModelDeleteView.as_view(), name='device_model_delete'),
]