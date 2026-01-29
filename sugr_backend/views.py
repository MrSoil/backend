import copy
import hashlib
import json
import uuid

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import (
    UserSerializer, UserReadSerializer, AdminUserReadSerializer, AdminUserUpdateSerializer,
    AdminPatientAccessSerializer,
    PatientDataSerializer, MedicineDataSerializer, FileDataSerializer,
)
from .models import FileData
from django.contrib.auth import get_user_model
from django.core import serializers

class RegisterUser(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class LoginUser(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            user_data = UserReadSerializer(user).data
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data,
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.permissions import AllowAny


class CustomTokenVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        auth_header = request.headers.get('Authorization') or ''
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != 'Bearer':
            return Response({'success': False}, status=401)
        token = parts[1]
        try:
            untyped = UntypedToken(token)
            user_id = untyped.get('user_id')
            if not user_id:
                return Response({'success': False}, status=401)
            user = get_user_model().objects.get(pk=user_id)
            user_data = UserReadSerializer(user).data
            return Response({'success': True, 'user': user_data})
        except (InvalidToken, TokenError, get_user_model().DoesNotExist):
            return Response({'success': False}, status=401)


from .models import PatientData, MedicineData, FileData
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from io import BytesIO
from PIL import Image
import base64


def get_accessible_patients_queryset(user):
    """Patients the user can access: own, allowed_users, or all if staff."""
    if getattr(user, 'is_staff', False):
        return PatientData.objects.all()
    return PatientData.objects.filter(Q(user=user) | Q(allowed_users=user)).distinct()

RESPONSE_TEMPLATE = {
    "Monday": {"drugs_data": [], "given_drugs": []},
    "Tuesday": {"drugs_data": [], "given_drugs": []},
    "Wednesday": {"drugs_data": [], "given_drugs": []},
    "Thursday": {"drugs_data": [], "given_drugs": []},
    "Friday": {"drugs_data": [], "given_drugs": []},
    "Saturday": {"drugs_data": [], "given_drugs": []},
    "Sunday": {"drugs_data": [], "given_drugs": []},
}


# def get_drug_id(input_json):
#     hash_object = hashlib.sha256()
#     hash_object.update(
#         str(input_json["drug_time"] +
#             input_json["drug_day"] +
#             input_json["drug_name"] +
#             input_json["drug_dose"] +
#             input_json["drug_desc"]).encode('utf-8'))
#     return hash_object.hexdigest()
#
#
# def get_given_drug_id(input_json):
#     hash_object = hashlib.sha256()
#     hash_object.update(
#         str(input_json["drug_time"] +
#             input_json["drug_day"] +
#             input_json["drug_name"] +
#             input_json["drug_dose"] +
#             input_json["given_date"] +
#             input_json["drug_desc"]).encode('utf-8'))
#     return hash_object.hexdigest()
#
#
# def get_note_id(input_json):
#     hash_object = hashlib.sha256()
#     hash_object.update(
#         str(input_json["note_date"] +
#             input_json["note_title"] +
#             input_json["note_data"]).encode('utf-8'))
#     return hash_object.hexdigest()


def get_object_id(input_str):
    hash_object = hashlib.sha256()
    hash_object.update(input_str.encode('utf-8'))
    return hash_object.hexdigest()


class PatientAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _user_email(self, request):
        return request.user.email if request.user and request.user.is_authenticated else None

    def post(self, request):
        request_data = dict(request.data)
        request_data.pop("email", None)
        request_type = request_data.pop("type")
        user = request.user

        if request_type == "new":
            patient_data = {
                "user": str(user.pk),
                "patient_id": request_data["patient_personal_info"]["section_1"]["citizenID"],
                "patient_personal_info": request_data["patient_personal_info"],
                "patient_medicines": request_data["patient_medicines"] if "patient_medicines" in request_data and
                                                                          request_data[
                                                                              "patient_medicines"] is not None else [],
                "patient_signed_hc": {} if "patient_signed_hc" in request_data and request_data[
                    "patient_signed_hc"] is not None else {},
                "patient_vitals": {} if "patient_vitals" in request_data and request_data[
                    "patient_vitals"] is not None else {},
                "patient_notes": {} if "patient_notes" in request_data and request_data[
                    "patient_notes"] is not None else {}
            }

            # image_data = request.data.get('patient_photo')
            # image = Image.open(BytesIO(base64.b64decode(image_data)))
            #
            # image_io = BytesIO()
            # image.save(image_io, 'PNG')
            # image_io.seek(0)
            # request_data["patient_photo"] = image_io

            serializer = PatientDataSerializer(data=patient_data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"status": "error", "data": serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        user = request.user
        qs = get_accessible_patients_queryset(user)

        if not patient_id:
            patient_data = qs
        else:
            patient_data = qs.filter(patient_id=patient_id)

        serializer = PatientDataSerializer(patient_data, many=True)

        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        request_data = dict(request.data)
        request_data.pop("email", None)
        request_type = request_data.pop("type")
        user = request.user
        email = user.email

        if request_type == "update_patient":
            try:
                patient_data = get_accessible_patients_queryset(user).get(patient_id=request_data["patient_id"])
                
                def clean_none_values(obj):
                    """Recursively remove None values from dict/list structures, replacing with empty dict"""
                    if isinstance(obj, dict):
                        cleaned = {}
                        for key, value in obj.items():
                            if value is None:
                                cleaned[key] = {}
                            elif isinstance(value, (dict, list)):
                                cleaned[key] = clean_none_values(value)
                            else:
                                cleaned[key] = value
                        return cleaned
                    elif isinstance(obj, list):
                        cleaned = []
                        for item in obj:
                            if item is None:
                                cleaned.append({})
                            elif isinstance(item, (dict, list)):
                                cleaned.append(clean_none_values(item))
                            else:
                                cleaned.append(item)
                        return cleaned
                    return obj
                
                # Update patient_personal_info if provided
                if "patient_personal_info" in request_data:
                    # Make a copy to avoid modifying the original request data
                    personal_info = copy.deepcopy(request_data["patient_personal_info"])
                    # Ensure patient_id is set in section_1
                    if "section_1" in personal_info:
                        personal_info["section_1"]["patient_id"] = patient_data.patient_id
                    
                    # Add metadata for file updates in section_1 (image)
                    if "section_1" in personal_info:
                        section_1 = personal_info["section_1"]
                        if "image" in section_1 and section_1["image"]:
                            if "_file_metadata" not in section_1:
                                section_1["_file_metadata"] = {}
                            if "image" not in section_1["_file_metadata"]:
                                section_1["_file_metadata"]["image"] = {}
                            section_1["_file_metadata"]["image"]["last_updated_by"] = email
                            section_1["_file_metadata"]["image"]["last_updated_date"] = timezone.now().isoformat()
                    
                    # Add metadata for file updates in section_4
                    if "section_4" in personal_info:
                        section_4 = personal_info["section_4"]
                        file_fields = [
                            'psychiatricMedPrescriptionFile',
                            'depressionScaleFile',
                            'mocaFile',
                            'miniCogFile',
                            'socialReportFile'
                        ]
                        
                        if "_file_metadata" not in section_4:
                            section_4["_file_metadata"] = {}
                        
                        for file_field in file_fields:
                            if file_field in section_4 and section_4[file_field]:
                                if file_field not in section_4["_file_metadata"]:
                                    section_4["_file_metadata"][file_field] = {}
                                section_4["_file_metadata"][file_field]["last_updated_by"] = email
                                section_4["_file_metadata"][file_field]["last_updated_date"] = timezone.now().isoformat()
                    
                    patient_data.patient_personal_info = personal_info
                
                # Update patient_medicines if provided
                if "patient_medicines" in request_data:
                    patient_data.patient_medicines = request_data["patient_medicines"]
                else:
                    # Clean existing patient_medicines to remove None values
                    if patient_data.patient_medicines:
                        patient_data.patient_medicines = clean_none_values(patient_data.patient_medicines)
                
                # Update patient_signed_hc if provided
                if "patient_signed_hc" in request_data:
                    patient_data.patient_signed_hc = request_data["patient_signed_hc"]
                else:
                    # Clean existing patient_signed_hc to remove None values
                    if patient_data.patient_signed_hc:
                        patient_data.patient_signed_hc = clean_none_values(patient_data.patient_signed_hc)
                
                # Update patient_vitals if provided
                if "patient_vitals" in request_data:
                    patient_data.patient_vitals = request_data["patient_vitals"]
                else:
                    # Clean existing patient_vitals to remove None values
                    if patient_data.patient_vitals:
                        patient_data.patient_vitals = clean_none_values(patient_data.patient_vitals)
                
                # Update patient_notes if provided
                if "patient_notes" in request_data:
                    patient_data.patient_notes = request_data["patient_notes"]
                else:
                    # Clean existing patient_notes to remove None values
                    if patient_data.patient_notes:
                        patient_data.patient_notes = clean_none_values(patient_data.patient_notes)
                
                # Ensure exit_info is not None (it can be None due to null=True, but JSONField doesn't accept None)
                if patient_data.exit_info is None:
                    patient_data.exit_info = {}
                elif patient_data.exit_info:
                    patient_data.exit_info = clean_none_values(patient_data.exit_info)

                patient_data.save()
                
                # Serialize the response
                serializer = PatientDataSerializer(patient_data)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
            except PatientData.DoesNotExist:
                return Response({"status": "error", "message": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                print(f"Error updating patient: {str(e)}")
                return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif request_type == "add_scheduled_medicine":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
            medicine_id = get_object_id(str(request_data["patient_id"]) + str(request_data["medicine_data"]))
            request_data["medicine_data"]["prepared_dates"] = {}
            request_data["medicine_data"]["given_dates"] = {"morning": {}, "noon": {}, "evening": {}}

            medicine = {
                "medicine_id": medicine_id,
                "medicine_data": request_data["medicine_data"],
            }
            if medicine_id in patient_data.patient_medicines:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                patient_data.patient_medicines[medicine_id] = medicine
            except Exception:
                patient_data.patient_medicines = {medicine_id: medicine}

            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_medicines}, status=status.HTTP_200_OK)
        elif request_type == "update_scheduled_medicine":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
            medicine_id = request_data.get("medicine_id")
            
            if not medicine_id or medicine_id not in patient_data.patient_medicines:
                return Response({"status": "failed", "error": "Medicine not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Get existing medicine to preserve prepared_dates and given_dates
            existing_medicine = patient_data.patient_medicines[medicine_id]
            updated_medicine_data = request_data["medicine_data"]
            
            # Preserve existing prepared_dates and given_dates if not provided
            if "prepared_dates" not in updated_medicine_data:
                updated_medicine_data["prepared_dates"] = existing_medicine["medicine_data"].get("prepared_dates", {})
            if "given_dates" not in updated_medicine_data:
                updated_medicine_data["given_dates"] = existing_medicine["medicine_data"].get("given_dates", {"morning": {}, "noon": {}, "evening": {}})
            # Handle end_date: remove if empty string, preserve if not provided
            if "end_date" in updated_medicine_data:
                if not updated_medicine_data["end_date"]:  # Empty string or None
                    updated_medicine_data.pop("end_date", None)  # Remove it
            elif "end_date" in existing_medicine["medicine_data"]:
                # Preserve existing end_date if not provided in update
                updated_medicine_data["end_date"] = existing_medicine["medicine_data"].get("end_date")
            
            # Update the medicine
            updated_medicine = {
                "medicine_id": medicine_id,
                "medicine_data": updated_medicine_data
            }
            
            try:
                patient_data.patient_medicines[medicine_id] = updated_medicine
                patient_data.save()
                return Response({"status": "success", "data": patient_data.patient_medicines}, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"Error updating medicine: {str(e)}")
                return Response({"status": "failed", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif request_type == "remove_scheduled_medicine":
            return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        elif request_type == "add_given_medicine":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

            medicine_id = request_data["medicine_id"]
            given_period = request_data["period"]
            given_dates = patient_data.patient_medicines[medicine_id]["medicine_data"]["given_dates"][given_period]

            # medicine = {
            #     "medicine_id": medicine_id,
            #     "given_date": request_data["today_date"],
            #     "given": request_data["given"],
            #     "medicine_data": medicine_data,
            # }

            date_obj = datetime.strptime(request_data["today_date"].split(" GMT")[0],
                                         "%a %b %d %Y %H:%M:%S").strftime("%d-%m-%y")
            # "Tue Apr 23 2024 01:53:24 GMT+0300 (GMT+03:00)"
            try:
                # Store timestamp object instead of just boolean
                given_dates[date_obj] = {
                    "timestamp": request_data["today_date"],
                    "given": True
                }
                patient_data.patient_medicines[medicine_id]["medicine_data"]["given_dates"][given_period] = given_dates
            except Exception:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
            patient_data.save()

            return Response({"status": "success", "data": patient_data.patient_medicines},
                            status=status.HTTP_200_OK)
        elif request_type == "add_prepared_medicine":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

            medicine_id = request_data["medicine_id"]
            med_prepared_dates = patient_data.patient_medicines[medicine_id]["medicine_data"]["prepared_dates"]
            for each_date in request_data["prepared_dates"]:
                date_obj = datetime.strptime(each_date.split(" GMT")[0],
                                             "%a %b %d %Y %H:%M:%S").strftime("%d-%m-%y")
                # "Tue Apr 23 2024 01:53:24 GMT+0300 (GMT+03:00)"
                med_prepared_dates[date_obj] = True

            try:
                patient_data.patient_medicines[medicine_id]["medicine_data"]["prepared_dates"] = med_prepared_dates
            except Exception:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

            patient_data.save()

            return Response({"status": "success", "data": patient_data.patient_medicines},
                            status=status.HTTP_200_OK)
        elif request_type == "add_signed_hc":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

            date_obj = datetime.strptime(request_data["today_date"].split(" GMT")[0],
                                         "%a %b %d %Y %H:%M:%S").strftime("%d-%m-%y")

            signed_hc_id = get_object_id(str(request_data["patient_id"]) + str(request_data["signed_hc_data"]))
            signed_hc_type = request_data["signed_hc_type"]

            signed_hc = {
                "signed_hc_id": signed_hc_id,
                "signed_hc_data": request_data["signed_hc_data"],
                "created_by": email,
                "insert_ts": request_data["today_date"]
            }

            if date_obj not in patient_data.patient_signed_hc:
                patient_data.patient_signed_hc[date_obj] = {signed_hc_type: [signed_hc, ]}
                patient_data.save()
                return Response({"status": "success", "data": patient_data.patient_signed_hc},
                                status=status.HTTP_201_CREATED)
            else:
                if signed_hc_type not in patient_data.patient_signed_hc[date_obj]:
                    patient_data.patient_signed_hc[date_obj][signed_hc_type] = [signed_hc, ]
                    patient_data.save()
                    return Response({"status": "success", "data": patient_data.patient_signed_hc},
                                    status=status.HTTP_201_CREATED)
                else:
                    return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

        elif request_type == "update_signed_hc":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

            date_obj = datetime.strptime(request_data["today_date"].split(" GMT")[0],
                                         "%a %b %d %Y %H:%M:%S").strftime("%d-%m-%y")

            signed_hc_type = request_data["signed_hc_type"]

            signed_hc = {
                "signed_hc_id": request_data["signed_hc_id"],
                "signed_hc_data": request_data["signed_hc_data"],
                "created_by": email,
                "insert_ts": request_data["today_date"]
            }

            latest_hc_updates = patient_data.patient_signed_hc[date_obj][signed_hc_type]
            latest_hc_updates.append(signed_hc)
            patient_data.patient_signed_hc[date_obj][signed_hc_type] = latest_hc_updates

            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_signed_hc}, status=status.HTTP_200_OK)
        elif request_type == "add_vitals":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Initialize patient_vitals if it doesn't exist
            if not patient_data.patient_vitals:
                patient_data.patient_vitals = {}
            
            # Store vitals as arrays of values, with each entry having a timestamp
            vitals_data = request_data.get("vitals_data", {})
            today_date = request_data.get("today_date", datetime.now().strftime("%a %b %d %Y %H:%M:%S"))
            date_obj = datetime.strptime(today_date.split(" GMT")[0], "%a %b %d %Y %H:%M:%S").strftime("%d-%m-%y")
            
            # Initialize each vital type if it doesn't exist
            vital_types = ["heart_beat", "oxygen", "stress", "sleep", "vitality"]
            for vital_type in vital_types:
                if vital_type not in patient_data.patient_vitals:
                    patient_data.patient_vitals[vital_type] = []
            
            # Add new vital values
            if "heart_beat" in vitals_data and vitals_data["heart_beat"]:
                patient_data.patient_vitals["heart_beat"].append({
                    "value": float(vitals_data["heart_beat"]),
                    "date": date_obj,
                    "timestamp": today_date
                })
            if "oxygen" in vitals_data and vitals_data["oxygen"]:
                patient_data.patient_vitals["oxygen"].append({
                    "value": float(vitals_data["oxygen"]),
                    "date": date_obj,
                    "timestamp": today_date
                })
            if "stress" in vitals_data and vitals_data["stress"]:
                patient_data.patient_vitals["stress"].append({
                    "value": float(vitals_data["stress"]),
                    "date": date_obj,
                    "timestamp": today_date
                })
            if "sleep" in vitals_data and vitals_data["sleep"]:
                patient_data.patient_vitals["sleep"].append({
                    "value": float(vitals_data["sleep"]),
                    "date": date_obj,
                    "timestamp": today_date
                })
            if "vitality" in vitals_data and vitals_data["vitality"]:
                patient_data.patient_vitals["vitality"].append({
                    "value": float(vitals_data["vitality"]),
                    "date": date_obj,
                    "timestamp": today_date
                })
            
            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_vitals}, status=status.HTTP_200_OK)
        elif request_type == "add_note":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Initialize patient_notes if it doesn't exist
            if not patient_data.patient_notes:
                patient_data.patient_notes = {}
            
            # Generate note ID
            note_id = get_object_id(str(request_data["patient_id"]) + str(request_data["note_title"]) + str(request_data["note_data"]) + str(request_data.get("today_date", datetime.now().strftime("%a %b %d %Y %H:%M:%S"))))
            
            today_date = request_data.get("today_date", datetime.now().strftime("%a %b %d %Y %H:%M:%S"))
            date_obj = datetime.strptime(today_date.split(" GMT")[0], "%a %b %d %Y %H:%M:%S").strftime("%d-%m-%y %H:%M:%S")
            
            note = {
                "note_id": note_id,
                "note_title": request_data["note_title"],
                "note_data": request_data["note_data"],
                "note_date": date_obj,
                "created_by": email,
                "timestamp": today_date
            }
            
            patient_data.patient_notes[note_id] = note
            patient_data.save()
            
            return Response({"status": "success", "data": patient_data.patient_notes}, status=status.HTTP_200_OK)
        elif request_type == "update_note":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
            
            note_id = request_data.get("note_id")
            date_obj = request_data.get("note_date")

            if not patient_data.patient_notes or note_id not in patient_data.patient_notes:
                return Response({"status": "failed", "error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
            
            today_date = request_data.get("today_date", datetime.now().strftime("%a %b %d %Y %H:%M:%S"))
            updated_date_obj = datetime.strptime(today_date.split(" GMT")[0], "%a %b %d %Y %H:%M:%S").strftime("%d-%m-%y %H:%M:%S")

            # Update note
            patient_data.patient_notes[note_id]["note_title"] = request_data.get("note_title", patient_data.patient_notes[note_id]["note_title"])
            patient_data.patient_notes[note_id]["note_data"] = request_data.get("note_data", patient_data.patient_notes[note_id]["note_data"])
            patient_data.patient_notes[note_id]["note_date"] = updated_date_obj
            patient_data.patient_notes[note_id]["updated_at"] = today_date

            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_notes}, status=status.HTTP_200_OK)

    def delete(self, request):
        # Try to get data from request body first (JSON), fall back to GET params
        if request.body:
            try:
                request_data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
            except (json.JSONDecodeError, AttributeError):
                request_data = dict(request.data) if hasattr(request, 'data') and request.data else dict(request.GET)
        else:
            request_data = dict(request.GET)

        if not request_data.get("type"):
            return Response({"error": "Request type must be provided."},
                            status=status.HTTP_400_BAD_REQUEST)

        request_type = request_data.get("type")
        patient_id = request_data.get("patient_id")
        if not patient_id:
            return Response({"error": "Patient ID must be provided."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        patient_data_list = list(get_accessible_patients_queryset(user).filter(patient_id=patient_id))
        if not patient_data_list:
            return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        
        patient_data = patient_data_list[0]

        if request_type == "delete_patient":
            # Save exit information before deleting
            exit_type = request_data.get("exit_type", "")
            exit_reason = request_data.get("exit_reason", "")
            if exit_type or exit_reason:
                patient_data.exit_info = {
                    "exit_type": exit_type,
                    "exit_reason": exit_reason
                }
                patient_data.save()
            
            patient_personal_info = patient_data.patient_personal_info
            patient_personal_info["section_1"] = None
            patient_personal_info["section_2"] = None
            patient_data.patient_personal_info = patient_personal_info
            patient_data.patient_id = uuid.uuid4()
            patient_data.user = None
            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_id}, status=status.HTTP_200_OK)
        elif request_type == "delete_medicines":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

            medicine_ids = request_data.get("medicine_ids", [])
            if not medicine_ids:
                return Response({"error": "medicine_ids must be provided."},
                                status=status.HTTP_400_BAD_REQUEST)

            patient_medicines = patient_data.patient_medicines
            for medicine_id in medicine_ids:
                if medicine_id in patient_medicines:
                    del patient_medicines[medicine_id]
            try:
                patient_data.patient_medicines = patient_medicines
            except Exception:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_medicines}, status=status.HTTP_200_OK)

        elif request_type == "delete_note":
            patient_data = get_accessible_patients_queryset(user).filter(patient_id=request_data["patient_id"]).first()
            if not patient_data:
                return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
            
            note_id = request_data.get("note_id")
            
            if not patient_data.patient_notes or note_id not in patient_data.patient_notes:
                return Response({"status": "failed", "error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)
            
            del patient_data.patient_notes[note_id]
            
            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_notes}, status=status.HTTP_200_OK)
        elif request_type == "delete_signed_hc":
            signed_hc = patient_data["signed_hc"]

            signed_hc_id = request.query_params.get('signed_hc_id', False)

            if not signed_hc_id:
                return Response({"error": "Note ID must be provided."},
                                status=status.HTTP_400_BAD_REQUEST)

            del signed_hc[signed_hc_id]
            patient_data.patient_signed_hc = signed_hc
            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_signed_hc},
                            status=status.HTTP_201_CREATED)


class MedicineAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_data = dict(request.data)
        request_data.pop("email", None)
        request_type = request_data.pop("type")
        user = request.user

        if request_type == "new":
            medicine_data = {
                "medicine_id": get_object_id(str(request_data["medicine_data"]["medicine_category"]) + str(
                    request_data["medicine_data"]["medicine_name"])),
                "medicine_data": request_data["medicine_data"]
            }

            serializer = MedicineDataSerializer(data=medicine_data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response({"status": "error", "data": serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        medicine_data = MedicineData.objects.all()
        serializer = MedicineDataSerializer(medicine_data, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)


def extract_files_from_patient_data(patient_data, user_email):
    """Extract files from PatientData and normalize them"""
    files = []
    patient_id = patient_data.patient_id
    personal_info = patient_data.patient_personal_info or {}
    section_1 = personal_info.get('section_1', {})
    section_2 = personal_info.get('section_2', {})
    section_3 = personal_info.get('section_3', {})
    section_4 = personal_info.get('section_4', {})
    
    patient_firstname = section_1.get('firstname', '')
    patient_lastname = section_1.get('lastname', '')
    
    # Helper to get uploaded_by from metadata or fallback to user_email
    def get_uploaded_by(section, field_name):
        metadata = section.get('_file_metadata', {})
        field_metadata = metadata.get(field_name, {})
        return field_metadata.get('last_updated_by', user_email)
    
    def extract_file_data(file_value):
        """Helper to extract file data from various formats"""
        if not file_value:
            return None, None
        
        # Handle dict format: {data: "...", filename: "..."}
        if isinstance(file_value, dict):
            file_data = file_value.get('data', '')
            filename = file_value.get('filename', '')
            print(f"    extract_file_data: dict format, data type: {type(file_data)}, data length: {len(str(file_data)) if file_data else 0}")
            if file_data and isinstance(file_data, str):
                cleaned_data = file_data.strip()
                if cleaned_data:  # Only return if not empty after strip
                    print(f"    extract_file_data: returning dict data, length: {len(cleaned_data)}")
                    return cleaned_data, filename
            print(f"    extract_file_data: dict format but no valid data")
            return None, None
        
        # Handle string format (direct base64 string)
        if isinstance(file_value, str):
            cleaned_data = file_value.strip()
            print(f"    extract_file_data: string format, length: {len(cleaned_data)}")
            if cleaned_data:  # Only return if not empty after strip
                print(f"    extract_file_data: returning string data, length: {len(cleaned_data)}")
                return cleaned_data, None
            print(f"    extract_file_data: string format but empty after strip")
            return None, None
        
        print(f"    extract_file_data: unknown format, type: {type(file_value)}")
        return None, None
    
    def is_base64_string(s):
        """Check if string looks like base64 data"""
        if not isinstance(s, str):
            return False
        # Remove whitespace
        s = s.strip()
        if len(s) < 50:  # Reduced minimum length
            return False
        # Base64 strings are typically long and contain only base64 characters
        import re
        base64_pattern = re.compile(r'^[A-Za-z0-9+/=\s]+$')
        # Allow some whitespace and check if it's mostly base64
        cleaned = re.sub(r'\s+', '', s)
        if len(cleaned) < 50:
            return False
        return base64_pattern.match(cleaned) is not None
    
    # Extract image from section_1
    image_data = section_1.get('image')
    file_data, _ = extract_file_data(image_data)
    if file_data and len(file_data) >= 50:  # Relaxed validation for images too
        # Get uploaded_by from metadata if available
        section_1_metadata = section_1.get('_file_metadata', {})
        image_metadata = section_1_metadata.get('image', {})
        uploaded_by = image_metadata.get('last_updated_by', user_email)
        uploaded_date = image_metadata.get('last_updated_date')
        
        files.append({
            "file_id": f"patient_{patient_id}_image",
            "source": "patient_data",
            "source_id": patient_id,
            "field_path": "section_1.image",
            "patient_id": patient_id,
            "patient_firstname": patient_firstname,
            "patient_lastname": patient_lastname,
            "file_name": f"{patient_firstname}_{patient_lastname}_photo.jpg",
            "file_category": "Özlük Dokümanları",
            "file_size": len(file_data) * 3 // 4,  # Approximate base64 size
            "uploaded_by": uploaded_by,
            "uploaded_date": uploaded_date,
            "file_data": file_data,
            "file_type": "image/jpeg"
        })
    
    # Extract files from section_4 - all known file fields
    file_fields = [
        ('psychiatricMedPrescriptionFile', 'psychiatricMedPrescriptionFileName', 'Sağlık Dosyaları'),
        ('depressionScaleFile', 'depressionScaleFileName', 'Sağlık Dosyaları'),
        ('mocaFile', 'mocaFileName', 'Sağlık Dosyaları'),
        ('miniCogFile', 'miniCogFileName', 'Sağlık Dosyaları'),
        ('socialReportFile', 'socialReportFileName', 'Sağlık Dosyaları'),
    ]
    
    for file_field, filename_field, category in file_fields:
        file_value = section_4.get(file_field)
        
        # Debug: Log what we're getting
        if file_value:
            print(f"Found {file_field} for patient {patient_id}, type: {type(file_value)}, length: {len(str(file_value)) if isinstance(file_value, str) else 'N/A'}")
        
        file_data, filename_from_dict = extract_file_data(file_value)
        
        # Add file if we have data (relaxed validation - trust that if it's in the field, it's valid)
        if file_data:
            print(f"Extracting {file_field} for patient {patient_id}, data length: {len(file_data)}")
            
            # Get filename - prefer from dict, then from filename_field, then default
            if filename_from_dict:
                filename = filename_from_dict
            else:
                filename = section_4.get(filename_field, '')
            
            if not filename:
                filename = f"{file_field}.pdf"
            
            # Accept any non-empty data (very relaxed validation)
            # Only log warning if data seems suspiciously short
            if len(file_data) < 50:
                print(f"Warning: File {file_field} for patient {patient_id} is very short ({len(file_data)} chars), but adding anyway")
            
            # Get uploaded_by from metadata if available
            section_4_metadata = section_4.get('_file_metadata', {})
            field_metadata = section_4_metadata.get(file_field, {})
            uploaded_by = field_metadata.get('last_updated_by', user_email)
            uploaded_date = field_metadata.get('last_updated_date')
            
            files.append({
                "file_id": f"patient_{patient_id}_{file_field}",
                "source": "patient_data",
                "source_id": patient_id,
                "field_path": f"section_4.{file_field}",
                "patient_id": patient_id,
                "patient_firstname": patient_firstname,
                "patient_lastname": patient_lastname,
                "file_name": filename,
                "file_category": category,
                "file_size": len(file_data) * 3 // 4,  # Approximate base64 size
                "uploaded_by": uploaded_by,
                "uploaded_date": uploaded_date,
                "file_data": file_data,
                "file_type": "application/pdf"  # Default to PDF
            })
        else:
            print(f"No valid file data found for {file_field} in patient {patient_id}")
    
    return files


class FileAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        email = user.email
        all_files = []
        
        patient_data_list = PatientData.objects.filter(user=user)
        
        for patient_data in patient_data_list:
            try:
                # Debug: Check if patient has personal_info
                personal_info = patient_data.patient_personal_info or {}
                print(f"Patient {patient_data.patient_id} has personal_info: {bool(personal_info)}")
                
                if personal_info:
                    section_4 = personal_info.get('section_4', {})
                    print(f"Patient {patient_data.patient_id} section_4 keys: {list(section_4.keys()) if section_4 else 'None'}")
                    
                    # Check each file field
                    file_fields_to_check = [
                        'psychiatricMedPrescriptionFile',
                        'depressionScaleFile',
                        'mocaFile',
                        'miniCogFile',
                        'socialReportFile'
                    ]
                    for field in file_fields_to_check:
                        file_value = section_4.get(field)
                        if file_value:
                            print(f"  {field}: type={type(file_value)}, has_data={bool(file_value)}")
                            if isinstance(file_value, str):
                                print(f"    String length: {len(file_value)}")
                            elif isinstance(file_value, dict):
                                print(f"    Dict keys: {list(file_value.keys())}")
                                if 'data' in file_value:
                                    print(f"    Data length: {len(str(file_value.get('data', '')))}")
                
                # Use the patient's user email for uploaded_by, or fallback to requesting user
                patient_user = patient_data.user
                patient_user_email = patient_user.email if patient_user else email
                extracted_files = extract_files_from_patient_data(patient_data, patient_user_email)
                print(f"Extracted {len(extracted_files)} files from patient {patient_data.patient_id}")
                all_files.extend(extracted_files)
            except Exception as e:
                # Log error but continue processing other patients
                import traceback
                print(f"Error extracting files from patient {patient_data.patient_id}: {str(e)}")
                print(traceback.format_exc())
                continue
        
        # Get files from FileData - only this user's files
        file_data_list = FileData.objects.filter(user=user)
        for file_data in file_data_list:
            all_files.append({
                "file_id": file_data.file_id,
                "source": "file_data",
                "source_id": file_data.file_id,
                "field_path": None,
                "patient_id": file_data.patient_id,
                "patient_firstname": file_data.patient_firstname,
                "patient_lastname": file_data.patient_lastname,
                "file_name": file_data.file_name,
                "file_category": file_data.file_category,
                "file_size": file_data.file_size,
                "uploaded_by": file_data.uploaded_by,
                "uploaded_date": file_data.uploaded_date.isoformat() if file_data.uploaded_date else None,
                "file_data": file_data.file_data,
                "file_type": file_data.file_type
            })
        
        return Response({"status": "success", "data": all_files}, status=status.HTTP_200_OK)

    def post(self, request):
        request_data = dict(request.data)
        request_data.pop("email", None)
        user = request.user
        email = user.email
        
        file_id = f"file_{uuid.uuid4().hex}"
        
        file_data = {
            "file_id": file_id,
            "user": str(user.pk),
            "patient_id": request_data.get("patient_id", ""),
            "patient_firstname": request_data.get("patient_firstname", ""),
            "patient_lastname": request_data.get("patient_lastname", ""),
            "file_name": request_data.get("file_name", ""),
            "file_category": request_data.get("file_category", ""),
            "file_size": request_data.get("file_size", 0),
            "uploaded_by": email,
            "file_data": request_data.get("file_data", ""),
            "file_type": request_data.get("file_type", "application/octet-stream")
        }
        
        serializer = FileDataSerializer(data=file_data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        request_data = dict(request.data)
        email = request.user.email
        file_id = request_data.get("file_id")
        source = request_data.get("source")
        source_id = request_data.get("source_id")
        field_path = request_data.get("field_path")
        
        if source == "patient_data":
            try:
                patient_data = PatientData.objects.get(patient_id=source_id, user=request.user)
                personal_info = patient_data.patient_personal_info or {}
                
                if field_path:
                    # Navigate to the field and update it
                    path_parts = field_path.split('.')
                    if len(path_parts) == 2:
                        section = path_parts[0]
                        field = path_parts[1]
                        
                        if section not in personal_info:
                            personal_info[section] = {}
                        
                        personal_info[section][field] = request_data.get("file_data", "")
                        
                        # Update filename if provided
                        if field.endswith("File") and "file_name" in request_data:
                            filename_field = field.replace("File", "FileName")
                            personal_info[section][filename_field] = request_data.get("file_name", "")
                        
                        # Store uploaded_by information in section metadata (for tracking who last updated)
                        # Since PatientData doesn't have uploaded_by field, we'll store it in a metadata field
                        if section not in personal_info:
                            personal_info[section] = {}
                        if "_file_metadata" not in personal_info[section]:
                            personal_info[section]["_file_metadata"] = {}
                        if field not in personal_info[section]["_file_metadata"]:
                            personal_info[section]["_file_metadata"][field] = {}
                        personal_info[section]["_file_metadata"][field]["last_updated_by"] = email
                        personal_info[section]["_file_metadata"][field]["last_updated_date"] = timezone.now().isoformat()
                        
                        patient_data.patient_personal_info = personal_info
                        patient_data.save()
                        
                        return Response({"status": "success"}, status=status.HTTP_200_OK)
            except PatientData.DoesNotExist:
                return Response({"status": "error", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        elif source == "file_data":
            # Update file in FileData (only if file belongs to user)
            try:
                file_data = FileData.objects.get(file_id=file_id, user=request.user)
                file_data.file_name = request_data.get("file_name", file_data.file_name)
                file_data.file_size = request_data.get("file_size", file_data.file_size)
                file_data.file_data = request_data.get("file_data", file_data.file_data)
                file_data.file_type = request_data.get("file_type", file_data.file_type)
                # Update uploaded_by to the user who is updating the file
                file_data.uploaded_by = email
                file_data.uploaded_date = timezone.now()
                file_data.save()
                
                return Response({"status": "success"}, status=status.HTTP_200_OK)
            except FileData.DoesNotExist:
                return Response({"status": "error", "error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"status": "error", "error": "Invalid source"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request_data = dict(request.data)
        file_id = request_data.get("file_id")
        source = request_data.get("source")
        source_id = request_data.get("source_id")
        field_path = request_data.get("field_path")
        
        if source == "patient_data":
            try:
                patient_data = PatientData.objects.get(patient_id=source_id, user=request.user)
                personal_info = patient_data.patient_personal_info or {}
                
                if field_path:
                    path_parts = field_path.split('.')
                    if len(path_parts) == 2:
                        section = path_parts[0]
                        field = path_parts[1]
                        
                        if section in personal_info and field in personal_info[section]:
                            personal_info[section][field] = ""
                            
                            # Also clear filename if it exists
                            if field.endswith("File"):
                                filename_field = field.replace("File", "FileName")
                                if filename_field in personal_info[section]:
                                    personal_info[section][filename_field] = ""
                            
                            patient_data.patient_personal_info = personal_info
                            patient_data.save()
                            
                            return Response({"status": "success"}, status=status.HTTP_200_OK)
            except PatientData.DoesNotExist:
                return Response({"status": "error", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        elif source == "file_data":
            try:
                file_data = FileData.objects.get(file_id=file_id, user=request.user)
                file_data.delete()
                return Response({"status": "success"}, status=status.HTTP_200_OK)
            except FileData.DoesNotExist:
                return Response({"status": "error", "error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"status": "error", "error": "Invalid source"}, status=status.HTTP_400_BAD_REQUEST)


# --- Admin API (is_staff only) ---
from rest_framework.permissions import IsAdminUser


class AdminUserList(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = get_user_model().objects.all().order_by('email')
        data = AdminUserReadSerializer(users, many=True).data
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class AdminUserDetail(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            user = get_user_model().objects.get(pk=pk)
        except get_user_model().DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        data = AdminUserReadSerializer(user).data
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            user = get_user_model().objects.get(pk=pk)
        except get_user_model().DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user.refresh_from_db()
            data = AdminUserReadSerializer(user).data
            return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
        return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class AdminPermissionsList(APIView):
    """Return list of all permission codes (for admin UI)."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        from .models import default_permission_codes
        all_codes = list(default_permission_codes())
        if "access_admin" not in all_codes:
            all_codes.append("access_admin")
        return Response({"status": "success", "data": sorted(all_codes)}, status=status.HTTP_200_OK)


class AdminPatientList(APIView):
    """List all patients with owner and allowed_users (for admin access management)."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        patients = PatientData.objects.all().select_related('user').prefetch_related('allowed_users')
        data = AdminPatientAccessSerializer(patients, many=True).data
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)


class AdminPatientAccessDetail(APIView):
    """PATCH: set which users can access this patient (allowed_users)."""
    permission_classes = [IsAdminUser]

    def patch(self, request, patient_id):
        user_ids = request.data.get('user_ids')
        if user_ids is None:
            return Response({"status": "error", "data": {"user_ids": "user_ids list required"}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = PatientData.objects.get(patient_id=patient_id)
        except PatientData.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        # Validate user_ids exist
        User = get_user_model()
        users = User.objects.filter(pk__in=user_ids)
        if users.count() != len(user_ids):
            return Response({"status": "error", "data": "Invalid user_ids"}, status=status.HTTP_400_BAD_REQUEST)
        patient.allowed_users.set(users)
        data = AdminPatientAccessSerializer(patient).data
        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
