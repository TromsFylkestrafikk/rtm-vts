import os
import logging
import requests
import django
import json
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from map.models import TransitInformation, ApiMetadata
from config import UserName_DATEX, Password_DATEX
from django.utils import timezone

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")
django.setup()

BaseURL = "https://datex-server-get-v3-1.atlas.vegvesen.no/"
logger = logging.getLogger(__name__)

"""
This script does an API call to VTS, and stores the information 
"""

class Command(BaseCommand):
    help = "Fetch transit information and store it in the database"

    def handle(self, *args, **kwargs):
        url = f"{BaseURL}datexapi/GetSituation/pullsnapshotdata/"
        # Retrieve the last modified date from the database
        last_modified_entry = ApiMetadata.objects.filter(key='last_modified_date').first()
        headers = {}
        if last_modified_entry:
            last_modified_date = last_modified_entry.value
            headers['If-Modified-Since'] = last_modified_date
            logger.info(f"Using If-Modified-Since header: {last_modified_date}")
        # Prepare headers with If-Modified-Since if available
        response = requests.get(url, auth=(UserName_DATEX, Password_DATEX), headers=headers)

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
                    area_name = None
                    if location_reference is not None:
                        area_name_element = location_reference.find(".//ns8:areaName", namespaces=namespaces)
                        if area_name_element is not None:
                            area_name_values = area_name_element.findall("common:values/common:value", namespaces=namespaces)
                            area_name_texts = [v.text for v in area_name_values if v.text]
                            area_name = ' '.join(area_name_texts) if area_name_texts else None
                    # Extract posList data
                    pos_list_raw = None
                    pos_list_coords = None
                    gml_line_string = location_reference.find(".//ns8:gmlLineString", namespaces=namespaces) if location_reference is not None else None
                    if gml_line_string is not None:
                        pos_list_raw = gml_line_string.findtext("ns8:posList", namespaces=namespaces)
                        if pos_list_raw:
                            # Parse the posList into coordinate pairs
                            coords = list(map(float, pos_list_raw.strip().split()))
                            positions = list(zip(coords[::2], coords[1::2]))
                            # Store positions as JSON string
                            pos_list_coords = json.dumps(positions)

                    # Extract transit service information
                    transit_service_information = situation.findtext("ns12:transitServiceInformation", namespaces=namespaces)
                    transit_service_type = situation.findtext("ns12:transitServiceType", namespaces=namespaces)
                    # Extract comment
                    comment = None
                    general_public_comment = situation.find("ns12:generalPublicComment", namespaces)
                    if general_public_comment is not None:
                        comment_values = general_public_comment.findall(".//common:value", namespaces)
                        comments = [cv.text for cv in comment_values if cv.text]
                        comment = ' '.join(comments) if comments else None
                    # Create and save the TransitInformation object
                    TransitInformation.objects.update_or_create(
                        situation_id=situation_id,
                        defaults={
                            'version': version,
                            'creation_time': creation_time or timezone.now(),
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
                        }
                    )
                    logger.info(f"Stored: {situation_id} ({latitude}, {longitude})")

                except Exception as e:
                    logger.exception(f"Error processing situation record ID {situation_id}: {e}")
            # After processing, get the Last-Modified header and save it
            last_modified = response.headers.get('Last-Modified')
            if last_modified:
                # Save or update the last modified date in the database
                ApiMetadata.objects.update_or_create(
                    key='last_modified_date',
                    defaults={'value': last_modified}
                )
                logger.info(f"Saved Last-Modified date: {last_modified}")
            else:
                logger.warning("No Last-Modified header found in the response.")    
            logger.info("Successfully stored all transit data!")
        elif response.status_code == 304:
            logger.info("data not modified")
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