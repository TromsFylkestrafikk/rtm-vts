from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.db import connection
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
    def test_transit_service_type_is_ferry_sqlite(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT transit_service_type FROM map_transitinformation")
            rows = cursor.fetchall()
        ferry_present = any(row[0] == 'ferry' for row in rows)
        self.assertTrue(ferry_present, "No 'ferry' found in 'transit_service_type' field")