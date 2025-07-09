from django.contrib.auth.models import AbstractUser
from django.db import models
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
    patient_given_medicines = JSONField()
    patient_signed_hc = JSONField()

    REQUIRED_FIELDS = ['user', 'patient_id', 'patient_personal_info', 'patient_medicines',
                       'patient_given_medicines', 'patient_signed_hc']
    def __str__(self):
        return self.patient_id


class User(AbstractUser):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'password']
