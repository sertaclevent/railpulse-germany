from django.db import migrations


def seed_default_station(apps, _schema_editor):
    Station = apps.get_model("trains", "Station")
    Station.objects.update_or_create(
        eva_number="8000261",
        defaults={
            "name": "Muenchen Hbf",
            "city": "Muenchen",
            "state": "Bayern",
            "country": "DE",
            "latitude": 48.140232,
            "longitude": 11.558335,
            "ds100": "MH",
            "short_description": "Default station for RailPulse Germany dashboard.",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("trains", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_station, migrations.RunPython.noop),
    ]
