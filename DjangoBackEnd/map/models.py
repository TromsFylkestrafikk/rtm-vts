from django.db import models
from django.utils import timezone

class TransitInformation(models.Model):
    situation_id = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    creation_time = models.DateTimeField(default=timezone.now)
    version_time = models.DateTimeField(null=True, blank=True)
    probability_of_occurrence = models.CharField(max_length=255, null=True, blank=True)
    severity = models.CharField(max_length=255, null=True, blank=True)
    source_country = models.CharField(max_length=255, null=True, blank=True)
    source_identification = models.CharField(max_length=255, null=True, blank=True)
    source_name = models.CharField(max_length=255, null=True, blank=True)
    source_type = models.CharField(max_length=255, null=True, blank=True)
    validity_status = models.CharField(max_length=255, null=True, blank=True)
    overall_start_time = models.DateTimeField(null=True, blank=True)
    overall_end_time = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_description = models.TextField(null=True, blank=True)
    road_number = models.CharField(max_length=255, null=True, blank=True)
    transit_service_information = models.TextField(null=True, blank=True)
    transit_service_type = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.road_number} - {self.transit_service_type} ({self.transit_service_information})"