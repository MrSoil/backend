from django.contrib import admin
from .models import FileData

# Register your models here.

@admin.register(FileData)
class FileDataAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_name', 'patient_firstname', 'patient_lastname', 'file_category', 'uploaded_by', 'uploaded_date')
    list_filter = ('file_category', 'uploaded_date')
    search_fields = ('file_name', 'patient_firstname', 'patient_lastname', 'uploaded_by')
