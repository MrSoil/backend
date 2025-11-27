# Generated manually for adding patient_vitals field

from django.db import migrations
import djongo.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sugr_backend', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientdata',
            name='patient_vitals',
            field=djongo.models.fields.JSONField(default=dict),
        ),
    ]

