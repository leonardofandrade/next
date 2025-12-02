from django.urls import path
from . import views

app_name = 'base_tables'

urlpatterns = [
    # Organization URLs
    path('organizations/', views.organization_list, name='organization_list'),
    path('organizations/create/', views.organization_create, name='organization_create'),
    path('organizations/<int:pk>/edit/', views.organization_edit, name='organization_edit'),
    path('organizations/<int:pk>/delete/', views.organization_delete, name='organization_delete'),
    
    # Agency URLs
    path('agencies/', views.agency_list, name='agency_list'),
    path('agencies/create/', views.agency_create, name='agency_create'),
    path('agencies/<int:pk>/edit/', views.agency_edit, name='agency_edit'),
    path('agencies/<int:pk>/delete/', views.agency_delete, name='agency_delete'),
    
    # Department URLs
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # AgencyUnit URLs
    path('agency-units/', views.agency_unit_list, name='agency_unit_list'),
    path('agency-units/create/', views.agency_unit_create, name='agency_unit_create'),
    path('agency-units/<int:pk>/edit/', views.agency_unit_edit, name='agency_unit_edit'),
    path('agency-units/<int:pk>/delete/', views.agency_unit_delete, name='agency_unit_delete'),
    
    # EmployeePosition URLs
    path('employee-positions/', views.employee_position_list, name='employee_position_list'),
    path('employee-positions/create/', views.employee_position_create, name='employee_position_create'),
    path('employee-positions/<int:pk>/edit/', views.employee_position_edit, name='employee_position_edit'),
    path('employee-positions/<int:pk>/delete/', views.employee_position_delete, name='employee_position_delete'),
    
    # ProcedureCategory URLs
    path('procedure-categories/', views.procedure_category_list, name='procedure_category_list'),
    path('procedure-categories/create/', views.procedure_category_create, name='procedure_category_create'),
    path('procedure-categories/<int:pk>/edit/', views.procedure_category_edit, name='procedure_category_edit'),
    path('procedure-categories/<int:pk>/delete/', views.procedure_category_delete, name='procedure_category_delete'),
    
    # CrimeCategory URLs
    path('crime-categories/', views.crime_category_list, name='crime_category_list'),
    path('crime-categories/create/', views.crime_category_create, name='crime_category_create'),
    path('crime-categories/<int:pk>/edit/', views.crime_category_edit, name='crime_category_edit'),
    path('crime-categories/<int:pk>/delete/', views.crime_category_delete, name='crime_category_delete'),
    
    # DeviceCategory URLs
    path('device-categories/', views.device_category_list, name='device_category_list'),
    path('device-categories/create/', views.device_category_create, name='device_category_create'),
    path('device-categories/<int:pk>/edit/', views.device_category_edit, name='device_category_edit'),
    path('device-categories/<int:pk>/delete/', views.device_category_delete, name='device_category_delete'),
    
    # DeviceBrand URLs
    path('device-brands/', views.device_brand_list, name='device_brand_list'),
    path('device-brands/create/', views.device_brand_create, name='device_brand_create'),
    path('device-brands/<int:pk>/edit/', views.device_brand_edit, name='device_brand_edit'),
    path('device-brands/<int:pk>/delete/', views.device_brand_delete, name='device_brand_delete'),
    
    # DeviceModel URLs
    path('device-models/', views.device_model_list, name='device_model_list'),
    path('device-models/create/', views.device_model_create, name='device_model_create'),
    path('device-models/<int:pk>/edit/', views.device_model_edit, name='device_model_edit'),
    path('device-models/<int:pk>/delete/', views.device_model_delete, name='device_model_delete'),
]