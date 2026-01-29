import datetime
import hashlib
import uuid
from collections import OrderedDict

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from sugr_backend.models import PatientData, MedicineData, FileData
from io import BytesIO
from PIL import Image
import base64

User = get_user_model()


class CustomJSONSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        if isinstance(obj, OrderedDict):
            # Convert OrderedDict to a regular dict
            return {k: v for k, v in obj.items()}
        return obj


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class PatientDataSerializer(serializers.ModelSerializer):
    patient_personal_info = serializers.JSONField(required=True, allow_null=True)
    patient_medicines = serializers.JSONField(required=False, allow_null=True)
    patient_signed_hc = serializers.JSONField(required=False, allow_null=True)
    patient_vitals = serializers.JSONField(required=False, allow_null=True)
    patient_notes = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = PatientData
        fields = '__all__'

    def create(self, validated_data):
        # image_data = validated_data.get('patient_photo', None)
        # image_io = None
        # if image_data:
        #     image_bytes = base64.b64decode(image_data)
        #     image = Image.open(BytesIO(image_bytes))
        #
        #     # Convert RGBA to RGB if necessary
        #     if image.mode == 'RGBA':
        #         image = image.convert('RGB')
        #
        #     # Convert image to file-like object
        #     image_io = BytesIO()
        #     image.save(image_io, format='JPEG')
        #     image_io.seek(0)
        #     image_name = f"{uuid.uuid4()}.jpg"
        #     tempfile = SimpleUploadedFile(image_name, image_io.read(), content_type='image/jpeg')

        patient = PatientData.objects.create(
            user=validated_data['user'],
            patient_id=validated_data['patient_id'],
            patient_personal_info=validated_data['patient_personal_info'],
            patient_medicines=validated_data['patient_medicines'],
            patient_signed_hc=validated_data['patient_signed_hc'],
            patient_vitals=validated_data.get('patient_vitals', {}),
            patient_notes=validated_data.get('patient_notes', {})
        )
        return patient


class MedicineDataSerializer(serializers.ModelSerializer):
    medicine_data = serializers.JSONField(required=True, allow_null=True)

    class Meta:
        model = MedicineData
        fields = '__all__'

    def create(self, validated_data):
        user = MedicineData.objects.create(
            medicine_id=validated_data['medicine_id'],
            medicine_data=validated_data['medicine_data']
        )
        return user


class FileDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileData
        fields = '__all__'

    def create(self, validated_data):
        file = FileData.objects.create(
            file_id=validated_data['file_id'],
            user=validated_data['user'],
            patient_id=validated_data['patient_id'],
            patient_firstname=validated_data['patient_firstname'],
            patient_lastname=validated_data['patient_lastname'],
            file_name=validated_data['file_name'],
            file_category=validated_data['file_category'],
            file_size=validated_data['file_size'],
            uploaded_by=validated_data['uploaded_by'],
            file_data=validated_data['file_data'],
            file_type=validated_data['file_type']
        )
        return file
