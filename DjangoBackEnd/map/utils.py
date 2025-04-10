import requests
import json
import polyline
from map.models import BusRoute, TransitInformation
from django.db import connection

def get_trip_geojson(from_place, to_place, num_trips=2):
    url = "https://api.entur.io/journey-planner/v3/graphql"
    headers = {
        'ET-Client-Name': 'TromsøFylkeskommune-svipper-Studenter',
        'Content-Type': 'application/json'
    }

    query = """
    {
    trip(
      from: {
        place: "%s"
      },
      to: {
        place: "%s"
      },
      numTripPatterns: %d,
    ) {
      tripPatterns {
        legs {
          mode
          distance
          line {
            id
            name
          }
          fromPlace {
            name
            quay {
              name
            }
            latitude
            longitude
          }
          toPlace {
            name
            quay {
              name
            }
            latitude
            longitude
          }
          pointsOnLink {
            points
          }
        }
      }
    }
  }
    """ % (from_place, to_place, num_trips)

    payload = {"query": query}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        geojson_features = []
        for trip_pattern in data['data']['trip']['tripPatterns']:
            for leg in trip_pattern['legs']:
                if 'pointsOnLink' in leg and leg['pointsOnLink']:
                    # Decode polyline points
                    points = polyline.decode(leg['pointsOnLink']['points'])
                    # Swap lat/lng to lng/lat for GeoJSON compliance
                    points = [(lng, lat) for lat, lng in points]
                    
                    line_name = leg['line'].get('name') if leg.get('line') else None
                    geojson_feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": points
                        },
                        "properties": {
                            "mode": leg['mode'].lower(),  # Lowercase for consistency
                            "lineName": line_name,
                            "distance": leg['distance']
                        }
                    }
                    geojson_features.append(geojson_feature)

        geojson = {
            "type": "FeatureCollection",
            "features": geojson_features
        }
        return geojson

    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error in get_trip_geojson: {e}")
        return None

def calculate_collisions_for_storage(distance_meters=20):
    """
    Calculates collisions using Raw SQL (SpatiaLite ST_Distance).
    Returns details needed for storing in the DetectedCollision model.
    Requires SpatiaLite + PROJ library correctly configured.

    Args:
        distance_meters (int): The tolerance distance in meters.

    Returns:
        list: A list of dictionaries, each containing:
              {'transit_id': int, 'route_id': int, 'transit_lon': float, 'transit_lat': float}
              Returns an empty list if no collisions are found or on error.
    """
    collision_data_for_storage = []
    print(f"Calculating collisions for storage (Tolerance: {distance_meters}m)...")
    try:
        # --- Use Raw SQL for Collision Detection ---
        projected_srid = 32633 # Example: UTM Zone 33N (Ensure this is correct!)

        try:
            transit_table = TransitInformation._meta.db_table
            route_table = BusRoute._meta.db_table
        except AttributeError as meta_err:
            print(f"Error getting table names: {meta_err}")
            return []

        with connection.cursor() as cursor:
            # SELECT IDs and transit coordinates
            sql = f"""
                SELECT
                    t.id AS transit_id,
                    r.id AS route_id,
                    ST_X(t.location) AS transit_lon,
                    ST_Y(t.location) AS transit_lat
                FROM
                    "{transit_table}" AS t
                INNER JOIN
                    "{route_table}" AS r ON t.location IS NOT NULL AND r.path IS NOT NULL
                WHERE
                    ST_Distance(
                        ST_Transform(t.location, %s),
                        ST_Transform(r.path, %s)
                    ) <= %s
            """
            cursor.execute(sql, [projected_srid, projected_srid, float(distance_meters)])

            # --- Process results into simpler dictionaries ---
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                # Directly create the dictionary needed for storage
                result_dict = dict(zip(columns, row))
                collision_data_for_storage.append(result_dict)
            # --- End result processing ---

        print(f"Calculated {len(collision_data_for_storage)} potential collisions.")
        return collision_data_for_storage

    except Exception as e:
        print(f"An error occurred during collision calculation for storage: {e}")
        # import traceback
        # traceback.print_exc()
        return []