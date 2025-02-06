from django.db import models
from django.utils import timezone

class TransitInformation(models.Model):
    """
    Field Values: Each row contains values for all the fields defined in your TransitInformation model:
    ID: The primary key (1, 2, 3, etc.).
    Situation ID: Unique identifiers, e.g., 2d37009c-dd0e-4345-80d3-44f8c5f5fdeb_1.
    Version: Version numbers, e.g., 1, 2.
    Creation Time: Timestamps, e.g., 2025-02-04 10:51:20.341591.
    Version Time: Timestamps, matching or close to creation times.
    Probability of Occurrence: Values like certain.
    Severity: Values like unknown, highest, etc.
    Source Details: Country (NO), identification, name (NPRA), type (roadAuthorities).
    Validity Status: Values like definedByValidityTimeSpec.
    Validity Times: Start and end times.
    Latitude and Longitude: Numerical values indicating geographical coordinates.
    Location Description: Text descriptions of locations.
    Road Number: Values like F769, F850, etc.
    Transit Service Information: Values like loadCapacityChanged, serviceSuspended.
    Transit Service Type: Values like ferry.
    """
    situation_id = models.CharField(max_length=255, unique=True)
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
    pos_list_raw = models.TextField(null=True, blank=True, help_text="Raw posList string from XML")
    pos_list_coords = models.TextField(null=True, blank=True, help_text="Parsed posList as JSON")

    def __str__(self):
        return f"{self.road_number} - {self.transit_service_type} ({self.transit_service_information})"