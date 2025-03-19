from django.shortcuts import render
from django.urls import path
from django.http import HttpResponse,JsonResponse
from django.template import loader
from .models import TransitInformation
from pyproj import CRS, Transformer
import ast  # Safe alternative to eval() for string-to-list conversion
from .utils import get_trip_geojson 
import os, json
from django.conf import settings

def serve_geojson(request):
    """Serve the pre-generated GeoJSON file instead of querying the database."""
    geojson_path = os.path.join(settings.BASE_DIR, 'output.geojson')
    print(f"GeoJSON path: {geojson_path}")
    if os.path.exists(geojson_path):
        with open(geojson_path, 'r') as file:
            geojson_data = json.load(file)
        return JsonResponse(geojson_data, safe=False)
    else:
        return JsonResponse({"error": "GeoJSON file not found"}, status=404)


def test_view(request):
    return JsonResponse({'message': 'Test path is working!'})

def map(request):
    template = loader.get_template('map.html')
    return HttpResponse(template.render())


def is_epsg_4326(lon, lat):
    """ Check if coordinates are already in EPSG:4326 (lat/lon) format. """
    return -180 <= lon <= 180 and -90 <= lat <= 90


def get_filter_options(request):
    '''
    Retrieve unique filter options for transit information.

    This function queries the database to retrieve unique values for **counties** and 
    **situation types** from the `TransitInformation` model. The results are returned 
    as a JSON response, making them useful for populating dropdown filters in a frontend UI.

    Parameters
    ----------
    request : HttpRequest
        The HTTP request object (not used in filtering, but required for Django views).

    Returns
    -------
    JsonResponse
        A JSON response containing two lists:
        - `counties` (list of str): Unique county names.
        - `situation_types` (list of str): Unique situation types.

    Notes
    -----
    - The function removes `None` or empty values from the lists before returning them.
    - Uses `distinct()` to ensure uniqueness in both `counties` and `situation_types`.

    Example
    -------
    Response:
    ```json
    {
        "counties": ["Oslo", "Bergen", "Trondheim"],
        "situation_types": ["roadwork", "accident", "closure"]
    }
    ```
    '''
    try:
        counties = TransitInformation.objects.values_list('area_name', flat=True).distinct()
        counties = [county for county in counties if county]
        
        situation_types = TransitInformation.objects.values_list('filter_used', flat=True).distinct()
        situation_types = [type for type in situation_types if type]
        
        severities = TransitInformation.objects.values_list('severity', flat=True).distinct()
        severities = [severity for severity in severities if severity]
        
        return JsonResponse({
            'counties': list(counties),
            'situation_types': list(situation_types),
            'severities': list(severities)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def location_geojson(request):
    '''
    Generate a GeoJSON response containing transit location data.

    This function retrieves transit location data from the database, filters it based on
    optional query parameters (county and situation type), and formats the data into a
    GeoJSON FeatureCollection. It supports both Point and LineString geometries, 
    transforming coordinates when necessary.

    Parameters
    ----------
    request : HttpRequest
        The HTTP request object containing optional GET parameters:
        - `county` (str, optional): Filters locations by county name.
        - `situation_type` (str, optional): Filters locations by situation type.

    Returns
    -------
    JsonResponse
        A JSON response containing the formatted GeoJSON data.

    Notes
    -----
    - Coordinates are stored in EPSG:25833 (UTM) and transformed to EPSG:4326 (WGS84) when needed.
    - If `latitude` and `longitude` are provided, a **Point** feature is created.
    - If `pos_list_coords` is provided, a **LineString** feature is created.
    - Errors in processing `pos_list_coords` are caught and printed.

    Example
    -------
    Request:
        GET /api/location_geojson?county=Oslo&situation_type=roadwork

    Response:
    ```json
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [10.7522, 59.9139]
                },
                "properties": {
                    "id": 1,
                    "name": "E6",
                    "description": "Roadwork near city center",
                    "severity": "High",
                    "comment": "Delayed traffic",
                    "county": "Oslo",
                    "situation_type": "roadwork"
                }
            }
        ],
        "transit_list": [
            {
                "id": 1,
                "name": "E6",
                "description": "Roadwork near city center",
                "coordinates": [10.7522, 59.9139]
            }
        ]
    }
    ```
    '''
    crs_25833 = CRS('EPSG:25833')
    crs_4326 = CRS('EPSG:4326')
    transformer = Transformer.from_crs(crs_25833, crs_4326, always_xy=True)
    county = request.GET.get('county', None)
    situation_type = request.GET.get('situation_type', None)
    severity = request.GET.get('severity')
    
    locations = TransitInformation.objects.all()  
    if county:
        locations = locations.filter(area_name=county)
    if situation_type:
        locations = locations.filter(filter_used=situation_type)
    if severity:
        locations = locations.filter(severity=severity)
    features = []
    transit_list = []

    for location in locations:
        # Process Point (if available)
        if location.latitude and location.longitude:
            lon, lat = location.longitude, location.latitude  # Get original values
            
            if not is_epsg_4326(lon, lat):  # Only transform if in UTM
                lon, lat = transformer.transform(lon, lat)

            transit_list.append({
                "id": location.id,
                "name": location.road_number,
                "description": location.location_description,
                "coordinates": [lon, lat]
            })

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "id": location.id,
                    "name": location.road_number,
                    "description": location.location_description,
                    "severity": location.severity,
                    "comment": location.comment,
                    "county": location.area_name,
                    "situation_type": location.filter_used
                }
            })

        # Process Road (LineString) if available
        if location.pos_list_coords:
            try:
                # Convert stored string to list of coordinates
                coord_list = ast.literal_eval(location.pos_list_coords)
                transformed_coords = []

                for coord in coord_list:
                    lon, lat = coord[0], coord[1]

                    if not is_epsg_4326(lon, lat):  # Only transform UTM coordinates
                        lon, lat = transformer.transform(lon, lat)

                    transformed_coords.append([lon, lat])

                # Only add LineString if there are valid transformed points
                if transformed_coords:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": transformed_coords
                        },
                        "properties": {
                            "id": location.id,
                            "name": location.road_number,
                            "description": location.location_description,
                            "severity": location.severity,
                            "comment": location.comment,
                            "county": location.area_name,
                            "situation_type": location.filter_used
                        }
                    })

            except Exception as e:
                print(f"Error processing pos_list_coords for {location.id}: {e}")

    geojson_data = {
        "type": "FeatureCollection",
        "features": features,
        "transit_list": transit_list
    }

    return JsonResponse(geojson_data)

def trip(request):
    if request.method == 'POST':
        from_place = request.POST.get('from')
        to_place = request.POST.get('to')

        # Example GeoJSON generation (replace with your actual logic)
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [10.7522, 59.9139],  # Example coordinates
                        [10.7522, 59.9239]
                    ]
                },
                "properties": {
                    "distance": "10 km",
                    "duration": "30 minutes"
                }
            }]
        }

        return JsonResponse({
            'geojson': geojson_data,
            'distance': '10 km',
            'duration': '30 minutes',
            'route_description': 'Sample route'
        })
    
    # Render the trip planning page for GET requests
    return render(request, 'trip.html')