import copy
import hashlib
import uuid

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import UserSerializer, PatientDataSerializer


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


from .models import PatientData
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


def get_drug_id(input_json):
    hash_object = hashlib.sha256()
    hash_object.update(
        str(input_json["drug_time"] +
            input_json["drug_day"] +
            input_json["drug_name"] +
            input_json["drug_dose"] +
            input_json["drug_desc"]).encode('utf-8'))
    return hash_object.hexdigest()


def get_given_drug_id(input_json):
    hash_object = hashlib.sha256()
    hash_object.update(
        str(input_json["drug_time"] +
            input_json["drug_day"] +
            input_json["drug_name"] +
            input_json["drug_dose"] +
            input_json["given_date"] +
            input_json["drug_desc"]).encode('utf-8'))
    return hash_object.hexdigest()


def get_note_id(input_json):
    hash_object = hashlib.sha256()
    hash_object.update(
        str(input_json["note_date"] +
            input_json["note_title"] +
            input_json["note_data"]).encode('utf-8'))
    return hash_object.hexdigest()


def get_signed_hc_id(input_json):
    hash_object = hashlib.sha256()
    hash_object.update(
        str(input_json["hc_date"] +
            input_json["hc_data"]).encode('utf-8'))
    return hash_object.hexdigest()


class PatientAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        request_data = dict(request.data)
        email = request_data.pop("email")
        request_type = request_data.pop("type")

        user = get_user_model().objects.get(email=email)

        if request_type == "new":
            request_data["user"] = user.id
            request_data["date_of_birth"] = datetime.strptime(request_data["date_of_birth"], "%Y-%m-%d").date()
            request_data["drugs_data"] = request_data.get("drugs_data", {})
            request_data["notes_data"] = request_data.get("notes_data", {})
            request_data["given_drugs"] = request_data.get("given_drugs", {})
            request_data["signed_hc"] = request_data.get("signed_hc", {})
            # image_data = request.data.get('patient_photo')
            # image = Image.open(BytesIO(base64.b64decode(image_data)))
            #
            # image_io = BytesIO()
            # image.save(image_io, 'PNG')
            # image_io.seek(0)
            # request_data["patient_photo"] = image_io

            print(request_data)
            serializer = PatientDataSerializer(data=request_data)
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
        print(serializer)
        print(serializer.data)

        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        request_data = dict(request.data)
        email = request_data.pop("email")
        request_type = request_data.pop("type")

        user = get_user_model().objects.get(email=email)

        patient_data = list(PatientData.objects.filter(user=user, patient_id=request_data["patient_id"]))[0]

        if request_type == "update_patient":
            patient_data.floor_no = request_data["floor_no"]
            patient_data.care_category = request_data["care_category"]
            patient_data.date_of_birth = request_data["date_of_birth"]
            patient_data.blood_type = request_data["blood_type"]
            patient_data.height = request_data["height"]
            patient_data.weight = request_data["weight"]
            patient_data.gender = request_data["gender"]

            patient_data.save()
            return Response({"status": "success", "data": patient_data}, status=status.HTTP_201_CREATED)

        elif request_type == "add_drug":
            drug_id = get_drug_id(request_data)
            drug = {
                "drug_id": drug_id,
                "drug_time": request_data["drug_time"],
                "drug_day": request_data["drug_day"],
                "drug_name": request_data["drug_name"],
                "drug_desc": request_data["drug_desc"],
                "drug_dose": request_data["drug_dose"],
            }
            if drug_id in patient_data.drugs_data:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

            patient_data.drugs_data[drug_id] = drug
            patient_data.save()
            return Response({"status": "success", "data": patient_data.drugs_data}, status=status.HTTP_201_CREATED)

        elif request_type == "add_given_drug":
            drug_id = get_given_drug_id(request_data)
            drug = {
                "drug_id": drug_id,
                "drug_time": request_data["drug_time"],
                "drug_day": request_data["drug_day"],
                "drug_name": request_data["drug_name"],
                "drug_desc": request_data["drug_desc"],
                "drug_dose": request_data["drug_dose"],
                "given_date": request_data["given_date"]
            }

            date_obj = datetime.strptime(request_data["given_date"].split(" GMT")[0], "%a %b %d %Y %H:%M:%S")
            # "Tue Apr 23 2024 01:53:24 GMT+0300 (GMT+03:00)"
            if (request_data["drug_day"] != datetime.today().now().strftime("%A")) \
                    or (date_obj.date() != datetime.today().date()) \
                    or (drug_id in patient_data.given_drugs):
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

            patient_data.given_drugs[drug_id] = drug
            patient_data.save()
            return Response({"status": "success", "data": patient_data.given_drugs}, status=status.HTTP_201_CREATED)

        elif request_type == "add_note":
            note_id = get_note_id(request_data)
            if note_id in patient_data.notes_data:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

            note = {
                "note_id": note_id,
                "note_date": request_data["note_date"],
                "note_title": request_data["note_title"],
                "note_data": request_data["note_data"],
            }
            patient_data.notes_data[note_id] = note
            patient_data.save()
            return Response({"status": "success", "data": patient_data.notes_data}, status=status.HTTP_201_CREATED)

        elif request_type == "add_signed_hc":
            signed_hc_id = get_signed_hc_id(request_data)
            if signed_hc_id in patient_data.signed_hc:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

            hc = {
                "signed_hc_id": signed_hc_id,
                "hc_date": [request_data["hc_date"], ],
                "hc_data": request_data["hc_data"],
            }
            patient_data.signed_hc[signed_hc_id] = hc
            patient_data.save()
            return Response({"status": "success", "data": patient_data.signed_hc}, status=status.HTTP_201_CREATED)

        elif request_type == "update_signed_hc":
            signed_hc_id = get_signed_hc_id(request_data)
            if signed_hc_id not in patient_data.signed_hc:
                return Response({"status": "failed"}, status=status.HTTP_400_BAD_REQUEST)

            hc = {
                "signed_hc_id": signed_hc_id,
                "hc_date": [request_data["hc_date"], ].extend(patient_data.signed_hc[signed_hc_id]['hc_date']),
                "hc_data": request_data["hc_data"],
            }
            patient_data.signed_hc[signed_hc_id] = hc
            patient_data.save()
            return Response({"status": "success", "data": patient_data.signed_hc}, status=status.HTTP_201_CREATED)

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
            patient_data.signed_hc = signed_hc
            patient_data.save()
            return Response({"status": "success", "data": patient_data.signed_hc}, status=status.HTTP_201_CREATED)
