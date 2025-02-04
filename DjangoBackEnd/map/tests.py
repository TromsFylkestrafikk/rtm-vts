from django.core.management import call_command
from django.test import TestCase
from unittest.mock import patch, MagicMock
from map.models import TransitInformation
import xml.etree.ElementTree as ET
# Create your tests here.
class FetchTransitInformationTest(TestCase):

    @patch("requests.get")
    def test_fetch_transit_information_api_failure(self, mock_get):
        """Test API failure handling."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with self.assertLogs("map.management.commands.get_transit_info", level="ERROR") as log:
            call_command("get_transit_info")
            self.assertIn("Error: 500", log.output[0])  # Should now work correctly
        
        self.assertEqual(TransitInformation.objects.count(), 0)