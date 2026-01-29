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
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='accessible_patients',
        blank=True,
        help_text='Kullanıcılar bu danışanı görebilir ve düzenleyebilir (sahip her zaman erişebilir).',
    )
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


def default_permission_codes():
    return [
        "view_dashboard", "view_patients", "view_drugs", "view_files",
        "edit_patient", "edit_patient_medicines", "edit_patient_notes",
        "edit_patient_hc", "edit_patient_vitals", "export_medications",
        "add_patient", "add_file", "edit_file", "delete_file",
        "view_patient_detail",
    ]


class User(AbstractUser):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    permission_codes = models.JSONField(default=default_permission_codes, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'password']

    def get_permission_codes(self):
        # Use stored permission_codes; only default when never saved (None).
        if self.permission_codes is None:
            base = list(default_permission_codes())
        else:
            base = list(self.permission_codes)
        if self.is_staff and "access_admin" not in base:
            base.append("access_admin")
        return base
