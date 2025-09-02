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
        print(user)
        print(password)

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
        print(user)
        print(user.pk)
        print(user.id)

        if request_type == "new":
            patient_data = {
                "user": str(user.pk),
                "patient_id": request_data["patient_personal_info"]["section_1"]["citizenID"],
                "patient_personal_info": request_data["patient_personal_info"],
                "patient_medicines": request_data["patient_medicines"] if "patient_medicines" in request_data and
                                                                          request_data[
                                                                              "patient_medicines"] is not None else [],
                "patient_signed_hc": {} if "patient_signed_hc" in request_data and request_data[
                    "patient_signed_hc"] is not None else {}
            }

            # image_data = request.data.get('patient_photo')
            # image = Image.open(BytesIO(base64.b64decode(image_data)))
            #
            # image_io = BytesIO()
            # image.save(image_io, 'PNG')
            # image_io.seek(0)
            # request_data["patient_photo"] = image_io

            print(request_data)
            print(patient_data)
            serializer = PatientDataSerializer(data=patient_data)
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
        patient_data = PatientData.objects.exclude(user__isnull=True)
        serializer = PatientDataSerializer(patient_data, many=True)
        print(type(serializer.data[0]["patient_personal_info"]["section_1"]))

        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        request_data = dict(request.data)
        email = request_data.pop("email")
        request_type = request_data.pop("type")

        user = get_user_model().objects.get(email=email)

        if request_type == "update_patient":
            patient_data = list(PatientData.objects.filter(user=user, patient_id=request_data["patient_id"]))[0]
            patient_data["patient_personal_info"] = request_data[
                "patient_personal_info"] if "patient_personal_info" in request_data else patient_data[
                "patient_personal_info"]
            patient_data["patient_medicines"] = request_data[
                "patient_medicines"] if "patient_medicines" in request_data else patient_data["patient_medicines"]
            patient_data["patient_signed_hc"] = request_data[
                "patient_signed_hc"] if "patient_signed_hc" in request_data else patient_data["patient_signed_hc"]
            patient_data["patient_personal_info"]["patient_id"] = patient_data["patient_id"]

            patient_data.save()
            return Response({"status": "success", "data": patient_data}, status=status.HTTP_200_OK)
        elif request_type == "add_scheduled_medicine":
            patient_data = list(PatientData.objects.filter(user=user, patient_id=request_data["patient_id"]))[0]
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
        elif request_type == "remove_scheduled_medicine":
            return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
        elif request_type == "add_given_medicine":
            patient_data = list(PatientData.objects.filter(user=user, patient_id=request_data["patient_id"]))[0]

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
                given_dates[date_obj] = True
                patient_data.patient_medicines[medicine_id]["medicine_data"]["given_dates"][given_period] = given_dates
            except Exception:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
            patient_data.save()

            return Response({"status": "success", "data": patient_data.patient_medicines},
                            status=status.HTTP_200_OK)
        elif request_type == "add_prepared_medicine":
            patient_data = list(PatientData.objects.filter(user=user, patient_id=request_data["patient_id"]))[0]

            medicine_id = request_data["medicine_id"]
            med_prepared_dates = patient_data.patient_medicines[medicine_id]["medicine_data"]["prepared_dates"]

            date_obj = datetime.strptime(request_data["today_date"].split(" GMT")[0],
                                         "%a %b %d %Y %H:%M:%S").strftime("%d-%m-%y")
            # "Tue Apr 23 2024 01:53:24 GMT+0300 (GMT+03:00)"
            try:
                med_prepared_dates[date_obj] = True
                patient_data.patient_medicines[medicine_id]["medicine_data"]["prepared_dates"] = med_prepared_dates
            except Exception:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)
            patient_data.save()

            return Response({"status": "success", "data": patient_data.patient_medicines},
                            status=status.HTTP_200_OK)
        elif request_type == "add_signed_hc":
            patient_data = list(PatientData.objects.filter(user=user, patient_id=request_data["patient_id"]))[0]

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
                return Response({"status": "success", "data": patient_data.patient_signed_hc}, status=status.HTTP_201_CREATED)
            else:
                if signed_hc_type not in patient_data.patient_signed_hc[date_obj]:
                    patient_data.patient_signed_hc[date_obj][signed_hc_type] = [signed_hc, ]
                    patient_data.save()
                    return Response({"status": "success", "data": patient_data.patient_signed_hc}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

        elif request_type == "update_signed_hc":
            patient_data = list(PatientData.objects.filter(user=user, patient_id=request_data["patient_id"]))[0]

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

    def delete(self, request):
        email = request.query_params.get('email', False)
        request_type = request.query_params.get('type', False)
        patient_id = request.query_params.get('patient_id', False)

        if not (email and request_type and patient_id):
            return Response({"error": "Email, Request Type and Patient ID must be provided."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.get(email=email)
        patient_data = list(PatientData.objects.filter(user=user, patient_id=patient_id))[0]

        if not patient_data:
            return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

        if request_type == "delete_patient":
            patient_data.user = None
            patient_data.first_name = None
            patient_data.last_name = None
            patient_data.patient_id = uuid.uuid4()
            patient_data.floor_no = None
            patient_data.device_id = uuid.uuid4()
            patient_data.contact_first_name = None
            patient_data.contact_last_name = None
            patient_data.contact_phone_no = None
            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_id}, status=status.HTTP_200_OK)
        elif request_type == "delete_drug":
            drugs_data = patient_data["drugs_data"]

            drug_id = request.query_params.get('drug_id', False)

            if not drug_id:
                return Response({"error": "Drug ID must be provided."},
                                status=status.HTTP_400_BAD_REQUEST)

            del drugs_data[drug_id]
            patient_data.drugs_data = drugs_data
            patient_data.save()
            return Response({"status": "success", "data": patient_data.drugs_data}, status=status.HTTP_201_CREATED)
        elif request_type == "delete_note":
            notes_data = patient_data["notes_data"]

            note_id = request.query_params.get('note_id', False)

            if not note_id:
                return Response({"error": "Note ID must be provided."},
                                status=status.HTTP_400_BAD_REQUEST)

            del notes_data[note_id]
            patient_data.notes_data = notes_data
            patient_data.save()
            return Response({"status": "success", "data": patient_data.notes_data}, status=status.HTTP_201_CREATED)
        elif request_type == "delete_signed_hc":
            signed_hc = patient_data["signed_hc"]

            signed_hc_id = request.query_params.get('signed_hc_id', False)

            if not signed_hc_id:
                return Response({"error": "Note ID must be provided."},
                                status=status.HTTP_400_BAD_REQUEST)

            del signed_hc[signed_hc_id]
            patient_data.patient_signed_hc = signed_hc
            patient_data.save()
            return Response({"status": "success", "data": patient_data.patient_signed_hc}, status=status.HTTP_201_CREATED)


class MedicineAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        request_data = dict(request.data)
        print(request_data)
        email = request_data.pop("email")
        request_type = request_data.pop("type")

        user = get_user_model().objects.get(email=email)

        if request_type == "new":
            medicine_data = {
                "medicine_id": get_object_id(str(request_data["medicine_data"]["medicine_category"]) + str(request_data["medicine_data"]["medicine_name"])),
                "medicine_data": request_data["medicine_data"]
            }

            print(request_data)
            print(medicine_data)
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
        print(serializer)
        print(serializer.data)

        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
