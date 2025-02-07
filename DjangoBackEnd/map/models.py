from django.db import models
from django.utils import timezone

class ApiMetadata(models.Model):
    """
    Model to store metadata related to API interactions.

    Fields:
    - key: A unique identifier for the metadata (e.g., 'last_modified_date').
    - value: The value associated with the key (e.g., a timestamp or any other relevant information).

    Purpose:
    - This model is used to keep track of metadata information such as the last time data was fetched from an external API.
    - It helps in optimizing API calls by storing and utilizing metadata like 'Last-Modified' dates for conditional requests.
    """
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}"

class TransitInformation(models.Model):
    """
    Model to store transit situation information fetched from the VTS (Vegtrafikksentralen) API.

    Fields:
    - situation_id: Unique identifier for the transit situation.
    - version: Version number of the situation record.
    - creation_time: Timestamp when the situation record was created.
    - version_time: Timestamp of the version of the situation record.
    - probability_of_occurrence: Likelihood of the situation occurring (e.g., 'certain', 'probable').
    - severity: Severity level of the situation (e.g., 'unknown', 'highest', 'low').
    - source_country: Country code of the source (e.g., 'NO' for Norway).
    - source_identification: Identification code of the source.
    - source_name: Name of the source (e.g., 'NPRA' for Norwegian Public Roads Administration).
    - source_type: Type of source (e.g., 'roadAuthorities').
    - validity_status: Status of the situation's validity (e.g., 'definedByValidityTimeSpec').
    - overall_start_time: Start time of the situation's validity period.
    - overall_end_time: End time of the situation's validity period.
    - latitude: Latitude coordinate of the situation location.
    - longitude: Longitude coordinate of the situation location.
    - location_description: Textual description of the location.
    - road_number: Identifier for the road (e.g., 'F769', 'F850').
    - area_name: Name of the area or county.
    - transit_service_information: Additional information about the transit service (e.g., 'loadCapacityChanged', 'serviceSuspended').
    - transit_service_type: Type of transit service (e.g., 'ferry').
    - pos_list_raw: Raw positional data as a string from the XML response.
    - pos_list_coords: Parsed positional data stored as JSON.
    - comment: Any additional comments or public remarks related to the situation.

    Purpose:
    - Stores detailed information about transit situations such as ferries, road closures, and other incidents.
    - Facilitates querying and displaying transit data on maps and in reports.
    - Helps in analyzing and monitoring transit situations over time.
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
    area_name = models.CharField(max_length=255, null=True, blank=True)
    transit_service_information = models.TextField(null=True, blank=True)
    transit_service_type = models.CharField(max_length=255, null=True, blank=True)
    pos_list_raw = models.TextField(null=True, blank=True, help_text="Raw posList string from XML")
    pos_list_coords = models.TextField(null=True, blank=True, help_text="Parsed posList as JSON")
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.road_number} - {self.transit_service_type} ({self.transit_service_information})"