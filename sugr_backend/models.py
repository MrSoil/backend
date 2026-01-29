from django.contrib.auth.models import AbstractUser
from django.db import models
from djongo import models as djongo_models  # important
from djongo.models import JSONField

from backend import settings


class MedicineData(models.Model):
    medicine_id = models.CharField(primary_key=True, max_length=255, unique=True)
    # models.AutoField(primary_key=True, unique=True)
    medicine_data = JSONField()

    REQUIRED_FIELDS = ['medicine_data']

    def __str__(self):
        return self.medicine_id

class PatientData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patients')
    patient_id = models.CharField(max_length=255, unique=True)

    patient_personal_info = JSONField()
    patient_medicines = JSONField()
    patient_signed_hc = JSONField()
    patient_vitals = JSONField(default=dict)
    patient_notes = JSONField(default=dict)
    exit_info = JSONField(default=dict, null=True, blank=True)

    REQUIRED_FIELDS = ['user', 'patient_id', 'patient_personal_info', 'patient_medicines',
                       'patient_signed_hc']
    def __str__(self):
        return self.patient_id


class FileData(models.Model):
    file_id = models.CharField(primary_key=True, max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='files')
    patient_id = models.CharField(max_length=255)
    patient_firstname = models.CharField(max_length=255)
    patient_lastname = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_category = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_by = models.CharField(max_length=255)
    uploaded_date = models.DateTimeField(auto_now_add=True)
    file_data = models.TextField()  # Base64 encoded file data
    file_type = models.CharField(max_length=255)

    REQUIRED_FIELDS = ['user', 'patient_id', 'file_name', 'file_category', 'file_data']

    def __str__(self):
        return self.file_id


class User(AbstractUser):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'password']
