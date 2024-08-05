import datetime
import hashlib
import uuid

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from sugr_backend.models import PatientData
from io import BytesIO
from PIL import Image
import base64

User = get_user_model()


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
    patient_vitals = serializers.JSONField(required=False, allow_null=True)
    patient_photo = serializers.JSONField(required=False, allow_null=True)
    contact_first_name = serializers.CharField(required=False, allow_null=True, max_length=255)
    contact_last_name = serializers.CharField(required=False, allow_null=True, max_length=255)
    contact_phone_no = serializers.CharField(required=False, allow_null=True, max_length=255)

    class Meta:
        model = PatientData
        fields = '__all__'
        # fields = ('id', 'user', 'first_name', 'last_name', 'device_id', 'patient_id', 'floor_no', 'drugs_data', 'notes_data', 'given_drugs')

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
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            device_id=validated_data['device_id'],
            patient_id=validated_data['patient_id'],
            floor_no=validated_data['floor_no'],
            care_category=validated_data['care_category'],
            date_of_birth=validated_data['date_of_birth'],
            blood_type=validated_data['blood_type'],
            height=validated_data['height'],
            weight=validated_data['weight'],
            gender=validated_data['gender'],
            drugs_data=validated_data['drugs_data'],
            notes_data=validated_data['notes_data'],
            given_drugs=validated_data['given_drugs'],
            patient_vitals=validated_data.get('patient_vitals',
                                              {
                                                  "heart_beat": [],
                                                  "oxygen": [],
                                                  "stress": [],
                                                  "sleep": [],
                                                  "vitality": []
                                              }),
            contact_first_name=validated_data.get('contact_first_name', None),
            contact_last_name=validated_data.get('contact_last_name', None),
            contact_phone_no=validated_data.get('contact_phone_no', None),
            patient_photo=validated_data.get('patient_photo', None)
        )
        return patient
