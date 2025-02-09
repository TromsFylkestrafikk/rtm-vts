import os
import logging
import requests
import django
import json
from dateutil.parser import isoparse
from datetime import timezone as dt_timezone
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from map.models import TransitInformation, ApiMetadata
from config import UserName_DATEX, Password_DATEX
from email.utils import format_datetime

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")
django.setup()

BaseURL = "https://datex-server-get-v3-1.atlas.vegvesen.no/datexapi/GetSituation/pullsnapshotdata/"
logger = logging.getLogger(__name__)

# Define namespaces
namespaces = {
    'ns0': 'http://datex2.eu/schema/3/messageContainer',
    'ns2': 'http://datex2.eu/schema/3/messageContainer',
    'ns12': 'http://datex2.eu/schema/3/situation',
    'ns8': 'http://datex2.eu/schema/3/locationReferencing',
    'common': 'http://datex2.eu/schema/3/common',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'def': 'http://datex2.eu/schema/3/common',  # Assign a prefix 'def' to default namespace
}

"""
This script is a Django management command that fetches transit situation data from the VTS (Vegtrafikksentralen) API,
processes the XML response, and stores the relevant information in the database.

Key functionalities:
- Makes a GET request to the VTS API endpoint to retrieve the latest transit situation data.
- Utilizes the 'If-Modified-Since' HTTP header to request data only if it has been updated since the last fetch, optimizing network usage.
- Parses the XML response using ElementTree and extracts data from each 'situationRecord' element.
- Extracts various fields including:
    - Situation ID and version
    - Creation time and version time
    - Probability of occurrence and severity
    - Source information (country, identification, name, type)
    - Validity period (status, overall start and end times)
    - Location details (latitude, longitude, description, road number, area name)
    - Transit service information (type and additional information)
    - Positional data (coordinates list)
    - Comments and public remarks
- Handles datetime parsing with timezone awareness, converting all times to UTC.
- Stores the extracted information in the 'TransitInformation' model, updating existing records or creating new ones based on the situation ID.
- After processing, updates the 'last_modified_date' in the 'ApiMetadata' model using the 'Last-Modified' response header or the 'publicationTime' from the XML, to be used in subsequent requests.
- Includes robust error handling and logging to track the script's operations and any issues that arise.

Usage:
- Run the script as a Django management command:
    python manage.py get_transit_info

Requirements:
- Valid VTS API credentials (UserName_DATEX and Password_DATEX) must be provided in the 'config' module.
- The 'dateutil' library is used for parsing ISO 8601 datetime strings (install with 'pip install python-dateutil' if necessary).
- Ensure that the 'map' app and its models ('TransitInformation' and 'ApiMetadata') are properly set up in your Django project.
"""
"""
Filters available:
        filters = [
            'AbnormalTraffic',
            'Accident',
            'Activity',
            'AnimalPresenceObstruction',
            'AuthorityOperation',
            'Conditions',
            'ConstructionWorks',
            'DisturbanceActivity',
            'EnvironmentalObstruction',
            'EquipmentOrSystemFault',
            'GeneralInstructionOrMessageToRoadUsers',
            'GeneralNetworkManagement',
            'GeneralObstruction',
            'GenericSituationRecord',
            'InfrastructureDamageObstruction',
            'MaintenanceWorks',
            'NetworkManagement',
            'NonWeatherRelatedRoadConditions',
            'PoorEnvironmentConditions',
            'PublicEvent',
            'ReroutingManagement',
            'RoadOrCarriagewayOrLaneManagement',
            'RoadsideAssistance',
            'ServiceDisruption',
            'SpeedManagement',
            'TransitInformation',
            'VehicleObstruction',
            'WeatherRelatedRoadConditions',
            'WinterDrivingManagement',
        ]
"""
class Command(BaseCommand):
    help = "Fetch transit information and store it in the database"

    def handle(self, *args, **kwargs):
        # Retrieve the last modified date from the database
        last_modified_entry = ApiMetadata.objects.filter(key='last_modified_date').first()
        headers = {}
        if last_modified_entry:
            last_modified_date = last_modified_entry.value
            headers['If-Modified-Since'] = last_modified_date
            logger.info(f"Using If-Modified-Since header: {last_modified_date}")
        url = f"{BaseURL}"
        try:
            # Prepare headers with If-Modified-Since if available
            response = requests.get(url, auth=(UserName_DATEX, Password_DATEX), headers=headers)
        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            return
        if response.status_code == 200:
            self.process_response(response)
            self.update_last_modified_date(response)
        elif response.status_code == 304:
            logger.info("data not modified!")
        else:
            logger.error(f"Error fetching data: HTTP {response.status_code}")

    def to_float(self, value):
        try:
            return float(value) if value else None
        except ValueError:
            return None
    def safe_parse_datetime(self, datetime_str):
        if datetime_str is None:
            return None
        try:
            # Parse the datetime string, including timezone information
            parsed_datetime = isoparse(datetime_str)
            # Ensure the datetime is timezone-aware and convert to UTC
            parsed_datetime = parsed_datetime.astimezone(dt_timezone.utc)
            return parsed_datetime
        except (ValueError, TypeError) as e:
            logger.error(f"Could not parse datetime '{datetime_str}': {e}")
            return None
    def process_response(self, response):
        """Parse the XML response, process situation records, and update the database."""
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
            return
        # Iterate over each situation record
        for situation in root.findall(".//ns12:situationRecord", namespaces):
            try:
                xsi_type = situation.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                situation_type = xsi_type.split(':')[-1] if xsi_type else 'Unknown'
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
                if location_reference is not None:
                    latitude = location_reference.findtext(".//ns8:latitude", namespaces=namespaces)
                    longitude = location_reference.findtext(".//ns8:longitude", namespaces=namespaces)
                    location_description = location_reference.findtext(".//ns8:locationDescription/common:values/common:value", namespaces=namespaces)
                    road_number = location_reference.findtext(".//ns8:roadInformation/ns8:roadNumber", namespaces=namespaces)
                    # Extract area name
                    area_name_element = location_reference.find(".//ns8:areaName", namespaces=namespaces)
                    area_name = None
                    if area_name_element is not None:
                        area_name_values = area_name_element.findall("common:values/common:value", namespaces=namespaces)
                        area_name_texts = [v.text for v in area_name_values if v.text]
                        area_name = ' '.join(area_name_texts) if area_name_texts else None

                    # Extract posList data
                    pos_list_raw = None
                    pos_list_coords = None
                    gml_line_string = location_reference.find(".//ns8:gmlLineString", namespaces=namespaces)
                    if gml_line_string is not None:
                        pos_list_raw = gml_line_string.findtext("ns8:posList", namespaces=namespaces)
                        if pos_list_raw:
                            # Parse the posList into coordinate pairs
                            coords = list(map(float, pos_list_raw.strip().split()))
                            positions = list(zip(coords[::2], coords[1::2]))
                            # Store positions as JSON string
                            pos_list_coords = json.dumps(positions)
                else:
                    latitude = None
                    longitude = None
                    location_description = None
                    road_number = None
                    area_name = None
                    pos_list_raw = None
                    pos_list_coords = None

                # Extract transit service information
                transit_service_information = situation.findtext("ns12:transitServiceInformation", namespaces=namespaces)
                transit_service_type = situation.findtext("ns12:transitServiceType", namespaces=namespaces)

                # Extract comment
                comment = None
                general_public_comment = situation.find("ns12:generalPublicComment", namespaces=namespaces)
                if general_public_comment is not None:
                    comment_values = general_public_comment.findall(".//common:value", namespaces=namespaces)
                    comments = [cv.text for cv in comment_values if cv.text]
                    comment = ' '.join(comments) if comments else None

                # Create and save the TransitInformation object
                TransitInformation.objects.update_or_create(
                    situation_id=situation_id,
                    defaults={
                        'version': version,
                        'creation_time': creation_time,
                        'version_time': version_time,
                        'probability_of_occurrence': probability_of_occurrence,
                        'severity': severity,
                        'source_country': source_country,
                        'source_identification': source_identification,
                        'source_name': source_name,
                        'source_type': source_type,
                        'validity_status': validity_status,
                        'overall_start_time': overall_start_time,
                        'overall_end_time': overall_end_time,
                        'latitude': self.to_float(latitude),
                        'longitude': self.to_float(longitude),
                        'location_description': location_description,
                        'road_number': road_number,
                        'area_name': area_name,
                        'transit_service_information': transit_service_information,
                        'transit_service_type': transit_service_type,
                        'pos_list_raw': pos_list_raw,
                        'pos_list_coords': pos_list_coords,
                        'comment': comment,
                        'filter_used': situation_type,
                    }
                )
                logger.info(f"Stored: {situation_id} ({latitude}, {longitude})")

            except Exception as e:
                logger.exception(f"Error processing situation record ID {situation_id}: {e}")
    def update_last_modified_date(self, response):
        """Update the last modified date in the database based on the response headers or XML content."""
        try:
            # Get the Last-Modified header from the response
            last_modified = response.headers.get('Last-Modified')
            if last_modified:
                # Use Last-Modified header as is
                logger.info(f"Saved Last-Modified date: {last_modified}")
                last_modified_date_to_save = last_modified
            else:
                # Attempt to extract publicationTime from the XML
                root = ET.fromstring(response.content)
                publication_time = root.findtext('./ns2:payload/def:publicationTime', namespaces=namespaces)
                if publication_time:
                    logger.debug(f"Extracted publicationTime: {publication_time}")
                    parsed_publication_time = self.safe_parse_datetime(publication_time)
                    if parsed_publication_time:
                        # Format datetime into HTTP-date format
                        last_modified_fallback = format_datetime(parsed_publication_time, usegmt=True)
                        last_modified_date_to_save = last_modified_fallback
                        logger.info(f"No Last-Modified header found. Using publicationTime as last modified date: {last_modified_fallback}")
                    else:
                        logger.warning("Could not parse publicationTime.")
                        last_modified_date_to_save = None
                else:
                    logger.warning("No Last-Modified header or publicationTime found in the response.")
                    last_modified_date_to_save = None

            # Save the last modified date if available
            if last_modified_date_to_save:
                ApiMetadata.objects.update_or_create(
                    key='last_modified_date',
                    defaults={'value': last_modified_date_to_save}
                )
                logger.info("Last modified date updated successfully.")
            else:
                logger.warning("Last modified date was not updated due to missing value.")

        except Exception as e:
            logger.error(f"Error updating last modified date: {e}")