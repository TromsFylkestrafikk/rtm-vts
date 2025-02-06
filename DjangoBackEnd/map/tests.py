from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from map.models import TransitInformation

class FetchTransitInformationTest(TestCase):

    @patch("requests.get")
    def test_fetch_transit_information_api_failure(self, mock_get):
        """Test API failure handling."""
        # Mock the API response to simulate a failure (HTTP 500)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Capture the logs during the execution of the management command
        with self.assertLogs("map.management.commands.get_transit_info", level="ERROR") as log:
            call_command("get_transit_info")
            # Adjusted assertion to match the actual log message
            self.assertIn("Error fetching data: HTTP 500", log.output[0])

        # Ensure no data has been saved to the database
        self.assertEqual(TransitInformation.objects.count(), 0)
    @patch("requests.get")
    def test_fetch_and_store_transit_information(self, mock_get):
        # Prepare the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <d2LogicalModel xmlns="http://datex2.eu/schema/3/messageContainer"
                        xmlns:ns12="http://datex2.eu/schema/3/situation"
                        xmlns:common="http://datex2.eu/schema/3/common"
                        xmlns:ns8="http://datex2.eu/schema/3/locationReferencing">
            <payloadPublication>
                <ns12:situation>
                    <ns12:situationRecord id="FERRY1" version="1">
                        <ns12:situationRecordCreationTime>2023-01-01T12:00:00Z</ns12:situationRecordCreationTime>
                        <ns12:transitServiceType>ferry</ns12:transitServiceType>
                        <!-- Additional necessary fields -->
                    </ns12:situationRecord>
                </ns12:situation>
            </payloadPublication>
        </d2LogicalModel>
        """  # Your test XML data
        mock_response.headers = {'Last-Modified': 'Wed, 21 Oct 2020 07:28:00 GMT'}
        mock_get.return_value = mock_response
        # Run your management command
        call_command('get_transit_info')
        self.assertEqual(TransitInformation.objects.count(), 1)
        transit_info = TransitInformation.objects.first()
        self.assertEqual(transit_info.transit_service_type, 'ferry')