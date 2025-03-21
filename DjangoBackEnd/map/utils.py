import requests
import json
import polyline

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