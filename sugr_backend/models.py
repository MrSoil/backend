from django.contrib.auth.models import AbstractUser
from django.db import models
from djongo.models import JSONField

from backend import settings


class PatientData(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patients')
    device_id = models.CharField(max_length=255, unique=True)

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    patient_id = models.CharField(max_length=255, unique=True)
    floor_no = models.CharField(max_length=255)
    care_category = models.CharField(max_length=255)
    date_of_birth = models.DateField(max_length=255)
    blood_type = models.CharField(max_length=255)
    height = models.CharField(max_length=255)
    weight = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)

    drugs_data = JSONField()
    notes_data = JSONField()
    given_drugs = JSONField()

    patient_vitals = JSONField()
    contact_first_name = models.CharField(max_length=255)
    contact_last_name = models.CharField(max_length=255)
    contact_phone_no = models.CharField(max_length=255)
    patient_photo = models.TextField()

    REQUIRED_FIELDS = ['user', 'first_name', 'last_name',
                       'device_id', 'patient_id', 'floor_no',
                       'care_category', 'date_of_birth', 'blood_type',
                       'height', 'weight', 'gender',
                       'drugs_data', 'notes_data', 'given_drugs']

    def __str__(self):
        return self.patient_id


class User(AbstractUser):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'password']
