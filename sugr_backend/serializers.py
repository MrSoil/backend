import datetime
import hashlib
import uuid
from collections import OrderedDict

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from sugr_backend.models import PatientData, MedicineData, FileData, default_permission_codes
from io import BytesIO
from PIL import Image
import base64

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    """Read-only user info for login/verify response and admin API."""
    permission_codes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_staff', 'permission_codes')
        read_only_fields = fields

    def get_permission_codes(self, obj):
        return obj.get_permission_codes()


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
            password=validated_data['password'],
        )
        user.permission_codes = default_permission_codes()
        user.save(update_fields=['permission_codes'])
        return user


class AdminUserReadSerializer(serializers.ModelSerializer):
    """Admin panel: return raw permission_codes from DB so edit/save reflects correctly."""
    permission_codes = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_staff', 'permission_codes')
        read_only_fields = fields


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """For PATCH: update permission_codes and is_staff only."""
    permission_codes = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('permission_codes', 'is_staff')


class AdminPatientAccessSerializer(serializers.Serializer):
    """Admin panel: list patient with owner and allowed_users for access management."""
    patient_id = serializers.CharField()
    patient_name = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source='user_id')
    owner_email = serializers.EmailField(source='user.email')
    allowed_user_ids = serializers.SerializerMethodField()

    def get_patient_name(self, obj):
        info = obj.patient_personal_info or {}
        section = info.get('section_1') or {}
        first = section.get('firstname', '') or ''
        last = section.get('lastname', '') or ''
        return f"{first} {last}".strip() or obj.patient_id

    def get_allowed_user_ids(self, obj):
        return list(obj.allowed_users.values_list('id', flat=True))


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
