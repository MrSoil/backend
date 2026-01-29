from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('verify/', views.CustomTokenVerifyView.as_view(), name='custom_token_verify'),
    path('patients/', views.PatientAPI.as_view(), name='patient-api'),
    path('medicines/', views.MedicineAPI.as_view(), name='medicine-api'),
    path('files/', views.FileAPI.as_view(), name='file-api'),
    # Admin API (is_staff only)
    path('admin/users/', views.AdminUserList.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', views.AdminUserDetail.as_view(), name='admin-user-detail'),
    path('admin/permissions/', views.AdminPermissionsList.as_view(), name='admin-permissions-list'),
    path('admin/patients/', views.AdminPatientList.as_view(), name='admin-patient-list'),
    path('admin/patients/<str:patient_id>/access/', views.AdminPatientAccessDetail.as_view(), name='admin-patient-access'),
]