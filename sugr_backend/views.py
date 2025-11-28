import copy
import hashlib
import json
import uuid

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import UserSerializer, PatientDataSerializer, MedicineDataSerializer

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
        user = get_user_model().objects.get(email=email)
        user = authenticate(email=email, password=password) if user else None

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.permissions import AllowAny


class CustomTokenVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.headers.get('Authorization', "").split(' ')[1]
        try:
            UntypedToken(token)
            return Response({'success': True})
        except (InvalidToken, TokenError) as e:
            return Response({'success': False}, status=401)


from .models import PatientData, MedicineData
from django.contrib.auth import get_user_model
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64

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
    permission_classes = [AllowAny]

    def post(self, request):
        request_data = dict(request.data)
        email = request_data.pop("email")
        request_type = request_data.pop("type")

        user = get_user_model().objects.get(email=email)

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
        email = request.query_params.get('email')
        patient_id = request.query_params.get('patient_id')

        if not email:
            return Response({"error": "email must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        if not patient_id:
            patient_data = PatientData.objects.exclude(user__isnull=True)
        else:
            patient_data = PatientData.objects.exclude(user__isnull=True).filter(patient_id=patient_id)

        serializer = PatientDataSerializer(patient_data, many=True)

        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        request_data = dict(request.data)
        email = request_data.pop("email")
        request_type = request_data.pop("type")

        user = get_user_model().objects.get(email=email)

        if request_type == "update_patient":
            try:
                patient_data = PatientData.objects.get(patient_id=request_data["patient_id"])
                
                # Update patient_personal_info if provided
                if "patient_personal_info" in request_data:
                    # Make a copy to avoid modifying the original request data
                    personal_info = copy.deepcopy(request_data["patient_personal_info"])
                    # Ensure patient_id is set in section_1
                    if "section_1" in personal_info:
                        personal_info["section_1"]["patient_id"] = patient_data.patient_id
                    patient_data.patient_personal_info = personal_info
                
                # Update patient_medicines if provided
                if "patient_medicines" in request_data:
                    patient_data.patient_medicines = request_data["patient_medicines"]
                
                # Update patient_signed_hc if provided
                if "patient_signed_hc" in request_data:
                    patient_data.patient_signed_hc = request_data["patient_signed_hc"]
                
                # Update patient_vitals if provided
                if "patient_vitals" in request_data:
                    patient_data.patient_vitals = request_data["patient_vitals"]
                
                # Update patient_notes if provided
                if "patient_notes" in request_data:
                    patient_data.patient_notes = request_data["patient_notes"]

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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]
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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]
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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]

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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]

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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]

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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]

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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]
            
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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]
            
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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]
            
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

        if not (request_data.get("email") and request_data.get("patient_id")):
            return Response({"error": "Email and Patient ID must be provided."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Try to get user, but don't fail if user doesn't exist (for delete_patient operation)
        try:
            user = get_user_model().objects.get(email=request_data["email"])
        except get_user_model().DoesNotExist:
            # For delete_patient, we can proceed without the user if patient exists
            user = None

        patient_data_list = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))
        if not patient_data_list:
            return Response({"status": "failed", "error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        
        patient_data = patient_data_list[0]

        if request_type == "delete_patient":
            patient_personal_info = patient_data.patient_personal_info
            patient_personal_info["section_1"] = None
            patient_personal_info["section_2"] = None
            patient_data.patient_personal_info = patient_personal_info
            patient_data.patient_id = uuid.uuid4()
            patient_data.user = None
            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_id}, status=status.HTTP_200_OK)
        elif request_type == "delete_medicines":
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]

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
            patient_data = list(PatientData.objects.filter(patient_id=request_data["patient_id"]))[0]
            
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
    permission_classes = [AllowAny]

    def post(self, request):
        request_data = dict(request.data)
        email = request_data.pop("email")
        request_type = request_data.pop("type")

        user = get_user_model().objects.get(email=email)

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
        email = request.query_params.get('email')

        if not email:
            return Response({"error": "email must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.get(email=email)
        medicine_data = MedicineData.objects
        serializer = MedicineDataSerializer(medicine_data, many=True)

        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
