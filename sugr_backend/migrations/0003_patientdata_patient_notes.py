# Generated manually for adding patient_notes field

from django.db import migrations
import djongo.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sugr_backend', '0002_patientdata_patient_vitals'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientdata',
            name='patient_notes',
            field=djongo.models.fields.JSONField(default=dict),
        ),
    ]


