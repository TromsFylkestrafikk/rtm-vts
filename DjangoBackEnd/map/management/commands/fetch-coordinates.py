import json
import polyline
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from django.core.management.base import BaseCommand

JSON_FILE_PATH = "/home/alexander/rtm-vts/DjangoBackEnd/route_coordinates.geojson"  # Output as .geojson

class Command(BaseCommand):
    help = "Fetch static bus route coordinates for all bus lines in Troms"

    def fetch_route_coordinates(self):
        uri = "https://api.entur.io/realtime/v2/vehicles/graphql"

        headers = {
            "ET-Client-Name": "troms-fylkeskommune-studenter",
        }

        route_query = gql("""
        query {
          serviceJourneys(codespaceId: "TRO") {
            id
            pointsOnLink {
              length
              points
            }
          }
        }
        """)

        transport = RequestsHTTPTransport(url=uri, headers=headers)
        client = Client(transport=transport, fetch_schema_from_transport=True)

        result = client.execute(route_query)
        print(f"Received data: {result}")

        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }

        if "serviceJourneys" in result and result["serviceJourneys"]:
            for route_data in result["serviceJourneys"]:
                points_on_link = route_data.get("pointsOnLink", None)

                # Check if pointsOnLink is None or doesn't contain points
                if points_on_link and points_on_link.get("points"):
                    encoded_points = points_on_link["points"]
                    decoded_coordinates = polyline.decode(encoded_points)

                    # Create a feature for the bus route
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[lon, lat] for lat, lon in decoded_coordinates]  # Ensure [longitude, latitude] order
                        },
                        "properties": {
                            "last_updated": "2025-03-21T08:48:18Z"  # Fake timestamp, adjust as needed
                        }
                    }

                    geojson_data["features"].append(feature)
                else:
                    # Handle the case where no points are available for this route
                    self.stdout.write(self.style.WARNING(f"No points data found for journey ID {route_data.get('id')}"))

            # Save all routes to a GeoJSON file
            with open(JSON_FILE_PATH, "w") as f:
                json.dump(geojson_data, f, indent=4)

            self.stdout.write(self.style.SUCCESS("Successfully fetched and saved all route coordinates as GeoJSON"))
        else:
            self.stdout.write(self.style.ERROR("No route data found for any bus line in Troms"))

    def handle(self, *args, **kwargs):
        self.fetch_route_coordinates()
