from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.template import loader
from .models import TransitInformation
from pyproj import CRS, Transformer
import ast  # Safe alternative to eval() for string-to-list conversion

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
    counties = TransitInformation.objects.values_list('area_name', flat=True).distinct()
    counties = [county for county in counties if county]
    
    situation_types = TransitInformation.objects.values_list('filter_used', flat=True).distinct()
    situation_types = [type for type in situation_types if type]
    
    return JsonResponse({
        'counties': list(counties),
        'situation_types': list(situation_types)
    })

def location_geojson(request):
    '''
    Generate a GeoJSON response containing transit location data.

    This function retrieves transit location data from the database, filters it based on
    optional query parameters (county and situation type), and formats the data into a
    GeoJSON FeatureCollection. It supports both **Point** and **LineString** geometries, 
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
    
    locations = TransitInformation.objects.all()  
    if county:
        locations = locations.filter(area_name=county)
    if situation_type:
        locations = locations.filter(filter_used=situation_type)
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
