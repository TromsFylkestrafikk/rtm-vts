import os
import logging
import requests
import django
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from map.models import TransitInformation
from config import UserName_DATEX, Password_DATEX
from django.utils import timezone

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")
django.setup()

BaseURL = "https://datex-server-get-v3-1.atlas.vegvesen.no/"
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Fetch transit information and store it in the database"

    def handle(self, *args, **kwargs):
        url = f"{BaseURL}datexapi/GetSituation/pullsnapshotdata/filter/TransitInformation"
        response = requests.get(url, auth=(UserName_DATEX, Password_DATEX))

        if response.status_code == 200:
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                logger.error(f"Error parsing XML: {e}")
                return

            # Define namespaces
            namespaces = {
                "ns2": "http://datex2.eu/schema/3/messageContainer",
                "ns12": "http://datex2.eu/schema/3/situation",
                "ns8": "http://datex2.eu/schema/3/locationReferencing",
                "common": "http://datex2.eu/schema/3/common",
            }

            # Iterate over each situation record
            for situation in root.findall(".//ns12:situationRecord", namespaces):
                try:
                    # Extract basic information
                    situation_id = situation.get("id")
                    version = situation.get("version")
                    creation_time = self.safe_parse_datetime(
                        situation.findtext("ns12:situationRecordCreationTime", namespaces=namespaces)
                    )
                    version_time = self.safe_parse_datetime(
                        situation.findtext("ns12:situationRecordVersionTime", namespaces=namespaces)
                    )
                    probability_of_occurrence = situation.findtext(
                        "ns12:probabilityOfOccurrence", namespaces=namespaces
                    )
                    severity = situation.findtext("ns12:severity", namespaces=namespaces)

                    # Extract source information
                    source = situation.find("ns12:source", namespaces=namespaces)
                    source_country = source.findtext("common:sourceCountry", namespaces=namespaces) if source is not None else None
                    source_identification = source.findtext("common:sourceIdentification", namespaces=namespaces) if source is not None else None
                    source_name = source.findtext("common:sourceName/common:values/common:value", namespaces=namespaces) if source is not None else None
                    source_type = source.findtext("common:sourceType", namespaces=namespaces) if source is not None else None

                    # Extract validity information
                    validity = situation.find("ns12:validity", namespaces=namespaces)
                    validity_status = validity.findtext("common:validityStatus", namespaces=namespaces) if validity is not None else None
                    overall_start_time = self.safe_parse_datetime(
                        validity.findtext("common:validityTimeSpecification/common:overallStartTime", namespaces=namespaces)
                    ) if validity is not None else None
                    overall_end_time = self.safe_parse_datetime(
                        validity.findtext("common:validityTimeSpecification/common:overallEndTime", namespaces=namespaces)
                    ) if validity is not None else None

                    # Extract location information
                    location_reference = situation.find("ns12:locationReference", namespaces=namespaces)
                    latitude = location_reference.findtext(".//ns8:latitude", namespaces=namespaces) if location_reference is not None else None
                    longitude = location_reference.findtext(".//ns8:longitude", namespaces=namespaces) if location_reference is not None else None
                    location_description = location_reference.findtext(".//ns8:locationDescription/common:values/common:value", namespaces=namespaces) if location_reference is not None else None
                    road_number = location_reference.findtext(".//ns8:roadInformation/ns8:roadNumber", namespaces=namespaces) if location_reference is not None else None

                    # Extract transit service information
                    transit_service_information = situation.findtext("ns12:transitServiceInformation", namespaces=namespaces)
                    transit_service_type = situation.findtext("ns12:transitServiceType", namespaces=namespaces)

                    # Create and save the TransitInformation object
                    TransitInformation.objects.create(
                        situation_id=situation_id,
                        version=version,
                        creation_time=creation_time or timezone.now(),
                        version_time=version_time,
                        probability_of_occurrence=probability_of_occurrence,
                        severity=severity,
                        source_country=source_country,
                        source_identification=source_identification,
                        source_name=source_name,
                        source_type=source_type,
                        validity_status=validity_status,
                        overall_start_time=overall_start_time,
                        overall_end_time=overall_end_time,
                        latitude=self.to_float(latitude),
                        longitude=self.to_float(longitude),
                        location_description=location_description,
                        road_number=road_number,
                        transit_service_information=transit_service_information,
                        transit_service_type=transit_service_type,
                    )
                    logger.info(f"Stored: {situation_id} ({latitude}, {longitude})")

                except Exception as e:
                    logger.error(f"Error processing situation record ID {situation_id}: {e}")

            logger.info("Successfully stored all transit data!")
        else:
            logger.error(f"Error fetching data: HTTP {response.status_code}")

    def to_float(self, value):
        try:
            return float(value) if value else None
        except ValueError:
            return None

    def safe_parse_datetime(self, datetime_str):
        try:
            return parse_datetime(datetime_str) if datetime_str else None
        except (ValueError, TypeError) as e:
            logger.error(f"Could not parse datetime '{datetime_str}': {e}")
            return None