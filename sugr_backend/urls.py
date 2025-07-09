from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('verify/', views.CustomTokenVerifyView.as_view(), name='custom_token_verify'),
    path('patients/', views.PatientAPI.as_view(), name='patient-api'),
    path('medicines/', views.MedicineAPI.as_view(), name='medicine-api'),
]