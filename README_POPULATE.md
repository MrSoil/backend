# Sample Data Population Script

This script populates the SUGR database with comprehensive sample data for testing and demonstration purposes.

## What It Creates

1. **Users** (3 total):
   - Admin user (`admin@sugr.com` / `admin123`)
   - Standard user (`user@sugr.com` / `user123`)
   - Example user (`example@sugr.com` / `example123`)

2. **Patients** (6 total):
   - 2 male patients for standard user
   - 2 female patients for standard user
   - 1 male patient for example user
   - 1 female patient for example user
   
   Each patient includes:
   - Complete personal information (section_1)
   - Contact person information (section_2)
   - Health and care information (section_3)
   - Psychological information (section_4)
   - All fields are filled with valid Turkish data

3. **Medicines**:
   - Loaded from `medicines.xlsx` file (created automatically if not exists)
   - 30+ sample medicines across various categories
   - Categories include: Ağrı Kesici, Diyabet, Tansiyon, Kolesterol, Mide, Antibiyotik, etc.

4. **Medicine Assignments**:
   - Each patient is assigned 2-4 random medicines
   - Medicines are scheduled for morning/noon/evening periods
   - Days of week are randomly assigned
   - Dosages and fullness options are set
   - Some medicines have end dates

5. **Notes**:
   - 2-4 notes per patient
   - Various note types (Hijyen, Beslenme, Pozisyon, etc.)

6. **Vitals**:
   - 5 days of historical vitals for each patient
   - Includes: heart_beat, oxygen, stress, sleep, vitality

## Requirements

- Django environment set up
- MongoDB running and accessible
- Python packages: `pandas`, `openpyxl` (for Excel support)

## Installation

If you need to install the Excel dependencies:

```bash
pip install pandas openpyxl
```

## Usage

From the `backend` directory:

```bash
python populate_sample_data.py
```

The script will:
1. Create users if they don't exist
2. Create patients with complete valid data
3. Create or load medicines from `medicines.xlsx`
4. Assign medicines to patients
5. Add notes and vitals

## Excel File Format

If you want to use your own Excel file, create `medicines.xlsx` in the `backend` directory with the following columns:

- `medicine_name`: Name of the medicine
- `medicine_category`: Category of the medicine

Example:
```
medicine_name,medicine_category
Aspirin,Ağrı Kesici
Parol,Ağrı Kesici
Metformin,Diyabet
```

## Notes

- The script is idempotent - running it multiple times won't create duplicates
- Existing users/patients/medicines are skipped
- All data uses valid Turkish names, cities, and formats
- Patient IDs are generated as valid Turkish citizen IDs (11 digits)
- All dates and timestamps are properly formatted

## Troubleshooting

**Error: "pandas is required"**
- Install pandas: `pip install pandas openpyxl`

**Error: "Cannot connect to MongoDB"**
- Ensure MongoDB is running
- Check database settings in `backend/settings.py`
- Verify connection credentials

**Error: "Excel file format incorrect"**
- Ensure the Excel file has columns: `medicine_name` and `medicine_category`
- Check that the file is not corrupted

## Output

After running, you'll see:
- Summary of created users, patients, and medicines
- Login credentials for all users
- Confirmation messages for each operation
