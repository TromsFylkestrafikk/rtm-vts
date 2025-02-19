# Generated by Django 5.1.5 on 2025-02-04 12:51

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TransitInformation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("situation_id", models.CharField(max_length=255)),
                ("version", models.CharField(max_length=255)),
                (
                    "creation_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("version_time", models.DateTimeField(blank=True, null=True)),
                (
                    "probability_of_occurrence",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("severity", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "source_country",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "source_identification",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "source_name",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "source_type",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "validity_status",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("overall_start_time", models.DateTimeField(blank=True, null=True)),
                ("overall_end_time", models.DateTimeField(blank=True, null=True)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                ("location_description", models.TextField(blank=True, null=True)),
                (
                    "road_number",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "transit_service_information",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "transit_service_type",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
            ],
        ),
    ]
