# Generated by Django 5.1.5 on 2025-03-18 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0009_transitinformation_filter_used"),
    ]

    operations = [
        migrations.AddField(
            model_name="transitinformation",
            name="closure_reason",
            field=models.TextField(
                blank=True, help_text="Reason for closure", null=True
            ),
        ),
        migrations.AddField(
            model_name="transitinformation",
            name="closure_type",
            field=models.CharField(
                blank=True, help_text="Type of closure", max_length=255, null=True
            ),
        ),
        migrations.AddField(
            model_name="transitinformation",
            name="is_road_closed",
            field=models.BooleanField(
                default=False, help_text="Indicates if the road is closed"
            ),
        ),
    ]
