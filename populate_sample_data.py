#!/usr/bin/env python
"""
Standalone script to populate the database with sample data.
This script creates:
- 2 users (1 standard user, 1 admin user)
- Multiple dummy patients (male and female) with complete valid data
- Medicines from an Excel file
- Assigns medicines to patients
- Adds notes and vitals to patients

Usage:
    python populate_sample_data.py
    python populate_sample_data.py --excel medicines.xlsx
"""

import os
import sys
import django
import hashlib
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from sugr_backend.models import PatientData, MedicineData
from django.utils import timezone

User = get_user_model()

# Turkish cities list
TURKISH_CITIES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin",
    "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale",
    "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum",
    "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Isparta", "Mersin",
    "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli",
    "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş",
    "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas",
    "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak",
    "Aksaray", "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan",
    "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce"
]

GENDERS = ["Erkek", "Kadın"]
MARITAL_STATUSES = ["Evli", "Bekar", "Dul", "Boşanmış"]
EDUCATION_STATUSES = [
    "Okuma/Yazma Bilmiyor", "Okuma/Yazma Biliyor", "İlkokul/Ortaokul",
    "Lise", "Üniversite", "Yüksek Öğretim"
]
WORK_STATUSES = ["Emekli", "Yarı Zamanlı", "Tam Zamanlı"]
INSURANCES = ["Sosyal Güvencesi Yok", "SGK", "SSK", "Özel"]
BLOOD_TYPES = ["A RH+", "B RH+", "AB RH+", "0 RH+", "A RH-", "B RH-", "AB RH-", "0 RH-"]
RELATION_DEGREES = ["1. Derece Akraba", "2. Derece Akraba", "3. Derece Akraba", "4. Derece Akraba", "Akraba Değil"]
MEAL_WITH_OPTIONS = ["Tek Başına", "Eşiyle", "Ailesiyle", "Bakıcısıyla", "Diğer"]
ON_GOING_CARE_OPTIONS = ["Aktif Yaşam", "Destekli Yaşam", "Hafıza Bakımı", "Palyatif Bakım"]
CARE_DEVICES = [
    "Oksijen Cihazı", "Mama Cihazı", "Walker/Baston", "Tekerlekli Sandalye",
    "Protez/Ortez", "İşitme cihazı", "Bez", "Yatak Malzemesi"
]

# Sample Turkish names
MALE_FIRST_NAMES = ["Ahmet", "Mehmet", "Ali", "Mustafa", "Hasan", "Hüseyin", "İbrahim", "İsmail", "Osman", "Yusuf"]
FEMALE_FIRST_NAMES = ["Ayşe", "Fatma", "Hatice", "Zeynep", "Emine", "Meryem", "Elif", "Şerife", "Hanife", "Zeliha"]
LAST_NAMES = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir",
              "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek"]


def get_object_id(input_str):
    """Generate object ID using SHA256 hash"""
    hash_object = hashlib.sha256()
    hash_object.update(input_str.encode('utf-8'))
    return hash_object.hexdigest()


def generate_citizen_id():
    """Generate a valid Turkish citizen ID (11 digits)"""
    # Turkish citizen IDs start with non-zero digit and have checksum
    # For dummy data, we'll generate a simple 11-digit number
    return str(random.randint(10000000000, 99999999999))


def generate_date_of_birth(min_age=65, max_age=95):
    """Generate a random date of birth"""
    age = random.randint(min_age, max_age)
    birth_date = datetime.now() - timedelta(days=age*365 + random.randint(0, 365))
    return birth_date.strftime("%Y-%m-%d")


def generate_phone():
    """Generate a Turkish phone number"""
    return f"0{random.randint(500, 599)}{random.randint(1000000, 9999999)}"


def create_base64_image_placeholder():
    """Create a minimal valid base64 image placeholder"""
    # A 1x1 transparent PNG in base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def create_user(email, first_name, last_name, password, is_staff=False, is_superuser=False):
    """Create a user"""
    try:
        user = User.objects.get(email=email)
        print(f"User {email} already exists, skipping...")
        return user
    except User.DoesNotExist:
        user = User.objects.create_user(
            email=email,
            username=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        print(f"✓ Created user: {email} ({'Admin' if is_superuser else 'Standard'})")
        return user


def create_patient_personal_info(gender, user_email):
    """Create complete patient personal info"""
    is_male = gender == "Erkek"
    first_name = random.choice(MALE_FIRST_NAMES if is_male else FEMALE_FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    citizen_id = generate_citizen_id()
    date_of_birth = generate_date_of_birth()
    birth_place = random.choice(TURKISH_CITIES)
    
    # Contact person info
    contact_first_name = random.choice(MALE_FIRST_NAMES + FEMALE_FIRST_NAMES)
    contact_last_name = random.choice(LAST_NAMES)
    contact_citizen_id = generate_citizen_id()
    contact_date_of_birth = generate_date_of_birth(min_age=30, max_age=70)
    contact_birth_place = random.choice(TURKISH_CITIES)
    contact_phone = generate_phone()
    
    return {
        "section_1": {
            "image": create_base64_image_placeholder(),
            "firstname": first_name,
            "lastname": last_name,
            "citizenID": citizen_id,
            "patient_id": citizen_id,  # Same as citizenID
            "motherName": random.choice(FEMALE_FIRST_NAMES),
            "fatherName": random.choice(MALE_FIRST_NAMES),
            "dateOfBirth": date_of_birth,
            "birthPlace": birth_place,
            "patientGender": gender,
            "currentRelation": random.choice(RELATION_DEGREES),
            "patientHeight": str(random.randint(150, 180)),
            "patientWeight": str(random.randint(50, 90)),
            "patientRoom": f"Oda - {random.randint(101, 999)}",
            "deviceID": f"DEV{random.randint(1000, 9999)}",
            "education": random.choice(EDUCATION_STATUSES),
            "workStatus": random.choice(WORK_STATUSES),
            "insurance": random.choice(INSURANCES),
            "income": str(random.randint(3000, 15000)),
            "backgroundInfo": f"{first_name} {last_name} için örnek arka plan bilgisi. Sağlık durumu genel olarak stabil.",
            "bloodType": random.choice(BLOOD_TYPES),
        },
        "section_2": {
            "contactFirstname": contact_first_name,
            "contactLastname": contact_last_name,
            "contactCitizenID": contact_citizen_id,
            "contactMotherName": random.choice(FEMALE_FIRST_NAMES),
            "contactFatherName": random.choice(MALE_FIRST_NAMES),
            "contactDateOfBirth": contact_date_of_birth,
            "contactBirthPlace": contact_birth_place,
            "contactPatientGender": random.choice(GENDERS),
            "contactCurrentRelationship": random.choice(MARITAL_STATUSES),
            "contactRelation": random.choice(RELATION_DEGREES),
            "contactEducation": random.choice(EDUCATION_STATUSES),
            "contactWorkStatus": random.choice(WORK_STATUSES),
            "contactPhone": contact_phone,
            "contactAddress": f"{random.choice(TURKISH_CITIES)} Mahallesi, {random.randint(1, 100)}. Sokak No: {random.randint(1, 50)}",
            "contactWorkAddress": f"{random.choice(TURKISH_CITIES)} İş Merkezi, Kat {random.randint(1, 10)}",
            "contactEmail": f"contact_{contact_first_name.lower()}_{contact_last_name.lower()}@example.com",
            "contactApply": "Evet"
        },
        "section_3": {
            "onGoingProblems": ["Yüksek Tansiyon", "Diyabet"],
            "oldProblems": ["Grip", "Soğuk Algınlığı"],
            "doctorContacts": [
                {"name": "Dr. Mehmet Yılmaz", "phone": generate_phone(), "specialty": "Kardiyoloji"},
                {"name": "Dr. Ayşe Demir", "phone": generate_phone(), "specialty": "Dahiliye"}
            ],
            "oldMedicines": ["Aspirin", "Parol"],
            "onGoingMedicines": ["Tansiyon İlacı", "Şeker İlacı"],
            "system1": "Normal",
            "system2": "Normal",
            "system3": "Normal",
            "system4": "Normal",
            "onGoingCare": random.choice(ON_GOING_CARE_OPTIONS),
            "oldCare": "Aktif Yaşam",
            "medicalState": "Stabil",
            "fallingStory": "Son 6 ayda düşme hikayesi yok",
            "balanceState": "İyi",
            "selectedDevices": random.sample(CARE_DEVICES, random.randint(0, 3)),
            "isThereFallStory": "Hayır",
            "dengeYurumeBozuklugu": "Hayır",
            "needsPhysicalSupport": random.choice(["Evet", "Hayır"]),
            "physicalSupportDetails": "Yürüteç kullanıyor" if random.choice([True, False]) else "",
            "nutritionType": random.choice(["Oral", "Enteral", "Parenteral"]),
            "nutritionOther": "",
            "specialDiet": random.choice(["Evet", "Hayır"]),
            "specialDietDetails": "Tuzsuz diyet" if random.choice([True, False]) else "",
            "oralEngel": random.choice(["Evet", "Hayır"]),
            "oralEngelDetails": "",
            "kiloKaybi6Ay": random.choice(["Evet", "Hayır"]),
            "kiloKaybiDetails": "",
            "mealsWith": random.choice(MEAL_WITH_OPTIONS),
            "mealsWithOther": "",
            "mainMealsPerDay": str(random.randint(2, 4)),
            "snacksPerDay": str(random.randint(0, 3)),
            "waterLitersPerDay": str(round(random.uniform(1.0, 3.0), 1)),
            "doesNotConsume": ["Alkol", "Sigara"],
            "allergies": ["Penisilin"] if random.choice([True, False]) else [],
            "favoriteFoods": ["Meyve", "Sebze", "Et"]
        },
        "section_4": {
            "psychIssues": random.choice(["Evet", "Hayır"]),
            "psychEvaluation": "Normal" if random.choice([True, False]) else "Değerlendirme gerekli",
            "psychiatricMedUse": random.choice(["Evet", "Hayır"]),
            "psychiatricMedPrescriptionFile": "",
            "psychiatricMedPrescriptionFileName": "",
            "psychiatricMedNoReason": "",
            "depressionScale": random.choice(["Evet", "Hayır"]),
            "depressionScaleFile": "",
            "depressionScaleFileName": "",
            "depressionScaleNoReason": "",
            "moca": random.choice(["Evet", "Hayır"]),
            "mocaFile": "",
            "mocaFileName": "",
            "mocaNoReason": "",
            "miniCog": random.choice(["Evet", "Hayır"]),
            "miniCogFile": "",
            "miniCogFileName": "",
            "miniCogNoReason": "",
            "socialReport": random.choice(["Evet", "Hayır"]),
            "socialReportFile": "",
            "socialReportFileName": "",
            "socialReportNoReason": ""
        }
    }


def create_patient(user, gender="Erkek"):
    """Create a patient with complete data"""
    personal_info = create_patient_personal_info(gender, user.email)
    citizen_id = personal_info["section_1"]["citizenID"]
    
    try:
        patient = PatientData.objects.get(patient_id=citizen_id)
        print(f"Patient {citizen_id} already exists, skipping...")
        return patient
    except PatientData.DoesNotExist:
        patient = PatientData.objects.create(
            user=user,
            patient_id=citizen_id,
            patient_personal_info=personal_info,
            patient_medicines={},
            patient_signed_hc={},
            patient_vitals={},
            patient_notes={}
        )
        print(f"✓ Created patient: {personal_info['section_1']['firstname']} {personal_info['section_1']['lastname']} ({gender})")
        return patient


def create_sample_excel_file(excel_path):
    """Create a sample Excel file with medicines"""
    try:
        import pandas as pd
    except ImportError:
        print("WARNING: pandas is not installed. Cannot create Excel file.")
        return False
    
    medicines_data = [
        {"medicine_name": "Aspirin", "medicine_category": "Ağrı Kesici"},
        {"medicine_name": "Parol", "medicine_category": "Ağrı Kesici"},
        {"medicine_name": "İbuprofen", "medicine_category": "Ağrı Kesici"},
        {"medicine_name": "Metformin", "medicine_category": "Diyabet"},
        {"medicine_name": "Insulin", "medicine_category": "Diyabet"},
        {"medicine_name": "Glibenklamid", "medicine_category": "Diyabet"},
        {"medicine_name": "Lisinopril", "medicine_category": "Tansiyon"},
        {"medicine_name": "Amlodipin", "medicine_category": "Tansiyon"},
        {"medicine_name": "Ramipril", "medicine_category": "Tansiyon"},
        {"medicine_name": "Atorvastatin", "medicine_category": "Kolesterol"},
        {"medicine_name": "Simvastatin", "medicine_category": "Kolesterol"},
        {"medicine_name": "Omeprazol", "medicine_category": "Mide"},
        {"medicine_name": "Pantoprazol", "medicine_category": "Mide"},
        {"medicine_name": "Amoksisilin", "medicine_category": "Antibiyotik"},
        {"medicine_name": "Sefaleksin", "medicine_category": "Antibiyotik"},
        {"medicine_name": "Sertralin", "medicine_category": "Antidepresan"},
        {"medicine_name": "Fluoksetin", "medicine_category": "Antidepresan"},
        {"medicine_name": "Warfarin", "medicine_category": "Kan İnceltici"},
        {"medicine_name": "Heparin", "medicine_category": "Kan İnceltici"},
        {"medicine_name": "Levotiroksin", "medicine_category": "Tiroid"},
        {"medicine_name": "Metoprolol", "medicine_category": "Kalp"},
        {"medicine_name": "Digoksin", "medicine_category": "Kalp"},
        {"medicine_name": "Furosemid", "medicine_category": "İdrar Söktürücü"},
        {"medicine_name": "Spironolakton", "medicine_category": "İdrar Söktürücü"},
        {"medicine_name": "Losartan", "medicine_category": "Tansiyon"},
        {"medicine_name": "Valsartan", "medicine_category": "Tansiyon"},
        {"medicine_name": "Montelukast", "medicine_category": "Astım"},
        {"medicine_name": "Salbutamol", "medicine_category": "Astım"},
        {"medicine_name": "Donepezil", "medicine_category": "Alzheimer"},
        {"medicine_name": "Memantin", "medicine_category": "Alzheimer"},
    ]
    
    df = pd.DataFrame(medicines_data)
    df.to_excel(excel_path, index=False)
    print(f"✓ Created sample Excel file: {excel_path}")
    return True


def load_medicines_from_excel(excel_path):
    """Load medicines from Excel file"""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas is required to read Excel files. Install it with: pip install pandas openpyxl")
        return []
    
    try:
        df = pd.read_excel(excel_path)
        
        # Expected columns: medicine_name, medicine_category
        required_columns = ['medicine_name', 'medicine_category']
        if not all(col in df.columns for col in required_columns):
            print(f"ERROR: Excel file must contain columns: {required_columns}")
            print(f"Found columns: {list(df.columns)}")
            return []
        
        medicines = []
        for _, row in df.iterrows():
            medicine_name = str(row['medicine_name']).strip()
            medicine_category = str(row['medicine_category']).strip()
            
            if medicine_name and medicine_category:
                medicines.append({
                    'medicine_name': medicine_name,
                    'medicine_category': medicine_category
                })
        
        print(f"✓ Loaded {len(medicines)} medicines from Excel file")
        return medicines
    except Exception as e:
        print(f"ERROR loading Excel file: {e}")
        return []


def create_medicine(medicine_name, medicine_category):
    """Create a medicine in the system"""
    medicine_id = get_object_id(str(medicine_category) + str(medicine_name))
    
    try:
        medicine = MedicineData.objects.get(medicine_id=medicine_id)
        return medicine
    except MedicineData.DoesNotExist:
        medicine = MedicineData.objects.create(
            medicine_id=medicine_id,
            medicine_data={
                "medicine_name": medicine_name,
                "medicine_category": medicine_category
            }
        )
        return medicine


def assign_medicine_to_patient(patient, medicine, periods=None, days=None, dosages=None, fullness_options=None, end_date=None):
    """Assign a medicine to a patient"""
    if periods is None:
        periods = {
            "morning": random.choice([True, False]),
            "noon": random.choice([True, False]),
            "evening": random.choice([True, False])
        }
        # Ensure at least one period is selected
        if not any(periods.values()):
            periods["morning"] = True
    
    if days is None:
        days_of_week = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        days = {
            "morning": random.sample(days_of_week, random.randint(1, 3)) if periods.get("morning") else [],
            "noon": random.sample(days_of_week, random.randint(1, 3)) if periods.get("noon") else [],
            "evening": random.sample(days_of_week, random.randint(1, 3)) if periods.get("evening") else []
        }
    
    if dosages is None:
        dosages = {
            "morning": random.randint(1, 3) if periods.get("morning") else 0,
            "noon": random.randint(1, 3) if periods.get("noon") else 0,
            "evening": random.randint(1, 3) if periods.get("evening") else 0
        }
    
    if fullness_options is None:
        fullness_options = {
            "morning": random.choice(["Aç İçilecek", "Tok İçilecek"]) if periods.get("morning") else "",
            "noon": random.choice(["Aç İçilecek", "Tok İçilecek"]) if periods.get("noon") else "",
            "evening": random.choice(["Aç İçilecek", "Tok İçilecek"]) if periods.get("evening") else ""
        }
    
    medicine_data = {
        "name": medicine.medicine_data["medicine_name"],
        "category": medicine.medicine_data["medicine_category"],
        "selected_periods": periods,
        "selected_days": days,
        "fullness_options": fullness_options,
        "medicine_dosage": dosages,
        "prepared_dates": {},
        "given_dates": {"morning": {}, "noon": {}, "evening": {}}
    }
    
    if end_date:
        medicine_data["end_date"] = end_date
    
    medicine_id = get_object_id(str(patient.patient_id) + str(medicine_data))
    
    if patient.patient_medicines is None:
        patient.patient_medicines = {}
    
    patient.patient_medicines[medicine_id] = {
        "medicine_id": medicine_id,
        "medicine_data": medicine_data
    }
    
    patient.save()
    return medicine_id


def add_note_to_patient(patient, user_email, title, note_data):
    """Add a note to a patient"""
    if patient.patient_notes is None:
        patient.patient_notes = {}
    
    today_date = datetime.now().strftime("%a %b %d %Y %H:%M:%S")
    date_obj = datetime.now().strftime("%d-%m-%y %H:%M:%S")
    
    note_id = get_object_id(str(patient.patient_id) + str(title) + str(note_data) + str(today_date))
    
    note = {
        "note_id": note_id,
        "note_title": title,
        "note_data": note_data,
        "note_date": date_obj,
        "created_by": user_email,
        "timestamp": today_date
    }
    
    patient.patient_notes[note_id] = note
    patient.save()
    return note_id


def add_vitals_to_patient(patient):
    """Add sample vitals to a patient"""
    if patient.patient_vitals is None:
        patient.patient_vitals = {}
    
    today_date = datetime.now().strftime("%a %b %d %Y %H:%M:%S")
    date_obj = datetime.now().strftime("%d-%m-%y")
    
    vital_types = ["heart_beat", "oxygen", "stress", "sleep", "vitality"]
    
    for vital_type in vital_types:
        if vital_type not in patient.patient_vitals:
            patient.patient_vitals[vital_type] = []
        
        # Add 3-5 days of vitals
        for days_ago in range(5, 0, -1):
            vital_date = datetime.now() - timedelta(days=days_ago)
            vital_date_str = vital_date.strftime("%a %b %d %Y %H:%M:%S")
            vital_date_obj = vital_date.strftime("%d-%m-%y")
            
            if vital_type == "heart_beat":
                value = random.randint(60, 100)
            elif vital_type == "oxygen":
                value = random.randint(95, 100)
            elif vital_type == "stress":
                value = random.randint(1, 10)
            elif vital_type == "sleep":
                value = round(random.uniform(5.0, 9.0), 1)
            elif vital_type == "vitality":
                value = random.randint(1, 10)
            else:
                value = random.randint(1, 100)
            
            patient.patient_vitals[vital_type].append({
                "value": value,
                "date": vital_date_obj,
                "timestamp": vital_date_str
            })
    
    patient.save()


def main():
    """Main function to populate sample data"""
    print("=" * 60)
    print("SUGR Sample Data Population Script")
    print("=" * 60)
    print()
    
    # Create users
    print("Creating users...")
    admin_user = create_user(
        email="admin@sugr.com",
        first_name="Admin",
        last_name="User",
        password="admin123",
        is_staff=True,
        is_superuser=True
    )
    
    standard_user = create_user(
        email="user@sugr.com",
        first_name="Standard",
        last_name="User",
        password="user123",
        is_staff=False,
        is_superuser=False
    )
    print()
    
    # Create default example user
    print("Creating default example user...")
    example_user = create_user(
        email="example@sugr.com",
        first_name="Örnek",
        last_name="Kullanıcı",
        password="example123",
        is_staff=False,
        is_superuser=False
    )
    print()
    
    # Create patients
    print("Creating patients...")
    patients = []
    
    # Create male patients
    for i in range(2):
        patient = create_patient(standard_user, gender="Erkek")
        patients.append(patient)
    
    # Create female patients
    for i in range(2):
        patient = create_patient(standard_user, gender="Kadın")
        patients.append(patient)
    
    # Create patients for example user
    example_patient_male = create_patient(example_user, gender="Erkek")
    example_patient_female = create_patient(example_user, gender="Kadın")
    patients.extend([example_patient_male, example_patient_female])
    print()
    
    # Load medicines from Excel
    print("Loading medicines from Excel...")
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medicines.xlsx")
    if not os.path.exists(excel_path):
        print(f"Excel file '{excel_path}' not found. Creating sample Excel file...")
        if create_sample_excel_file(excel_path):
            medicines_data = load_medicines_from_excel(excel_path)
        else:
            print("Using default medicines list...")
            medicines_data = [
                {"medicine_name": "Aspirin", "medicine_category": "Ağrı Kesici"},
                {"medicine_name": "Parol", "medicine_category": "Ağrı Kesici"},
                {"medicine_name": "Metformin", "medicine_category": "Diyabet"},
                {"medicine_name": "Insulin", "medicine_category": "Diyabet"},
                {"medicine_name": "Lisinopril", "medicine_category": "Tansiyon"},
                {"medicine_name": "Amlodipin", "medicine_category": "Tansiyon"},
                {"medicine_name": "Atorvastatin", "medicine_category": "Kolesterol"},
                {"medicine_name": "Omeprazol", "medicine_category": "Mide"},
                {"medicine_name": "Amoksisilin", "medicine_category": "Antibiyotik"},
                {"medicine_name": "Sertralin", "medicine_category": "Antidepresan"},
            ]
    else:
        medicines_data = load_medicines_from_excel(excel_path)
        if not medicines_data:
            print("WARNING: No medicines loaded from Excel. Using default medicines...")
            medicines_data = [
                {"medicine_name": "Aspirin", "medicine_category": "Ağrı Kesici"},
                {"medicine_name": "Parol", "medicine_category": "Ağrı Kesici"},
            ]
    print()
    
    # Create medicines in system
    print("Creating medicines in system...")
    medicines = []
    for med_data in medicines_data:
        medicine = create_medicine(med_data["medicine_name"], med_data["medicine_category"])
        medicines.append(medicine)
        print(f"✓ Created medicine: {med_data['medicine_name']} ({med_data['medicine_category']})")
    print()
    
    # Assign medicines to patients
    print("Assigning medicines to patients...")
    for patient in patients:
        # Assign 2-4 random medicines to each patient
        num_medicines = random.randint(2, min(4, len(medicines)))
        selected_medicines = random.sample(medicines, num_medicines)
        
        for medicine in selected_medicines:
            # Some medicines have end dates
            end_date = None
            if random.choice([True, False]):
                end_date = (datetime.now() + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d")
            
            medicine_id = assign_medicine_to_patient(patient, medicine, end_date=end_date)
            print(f"✓ Assigned {medicine.medicine_data['medicine_name']} to {patient.patient_personal_info['section_1']['firstname']} {patient.patient_personal_info['section_1']['lastname']}")
    print()
    
    # Add notes to patients
    print("Adding notes to patients...")
    note_titles = [
        "Hijyen Gereksinimleri",
        "Beslenme Takibi",
        "Pozisyon Takibi",
        "Pansuman ve Katater Bakımı",
        "Ödem Takibi",
        "Misafir Güvenliği",
        "Genel Durum",
        "İlaç Takibi"
    ]
    
    for patient in patients:
        num_notes = random.randint(2, 4)
        selected_titles = random.sample(note_titles, num_notes)
        
        for title in selected_titles:
            note_data = f"{patient.patient_personal_info['section_1']['firstname']} {patient.patient_personal_info['section_1']['lastname']} için {title} notu. Detaylı bilgiler burada yer alabilir."
            add_note_to_patient(patient, standard_user.email, title, note_data)
            print(f"✓ Added note '{title}' to {patient.patient_personal_info['section_1']['firstname']} {patient.patient_personal_info['section_1']['lastname']}")
    print()
    
    # Add vitals to patients
    print("Adding vitals to patients...")
    for patient in patients:
        add_vitals_to_patient(patient)
        print(f"✓ Added vitals to {patient.patient_personal_info['section_1']['firstname']} {patient.patient_personal_info['section_1']['lastname']}")
    print()
    
    print("=" * 60)
    print("Sample data population completed successfully!")
    print("=" * 60)
    print()
    print("Created:")
    print(f"  - {User.objects.count()} users (including admin, standard, and example)")
    print(f"  - {PatientData.objects.count()} patients")
    print(f"  - {MedicineData.objects.count()} medicines")
    print()
    print("Login credentials:")
    print("  Admin: admin@sugr.com / admin123")
    print("  Standard: user@sugr.com / user123")
    print("  Example: example@sugr.com / example123")
    print()


if __name__ == "__main__":
    main()
