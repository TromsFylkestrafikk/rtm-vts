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


def location_geojson(request):
    crs_25833 = CRS('EPSG:25833')
    crs_4326 = CRS('EPSG:4326')
    transformer = Transformer.from_crs(crs_25833, crs_4326, always_xy=True)

    # Get the county parameter from the URL query
    county = request.GET.get('county', None)  # Default to None if no county is selected

    # Filter locations by county if provided
    if county:
        locations = TransitInformation.objects.filter(county__iexact=county)  # Case-insensitive match for county
    else:
        locations = TransitInformation.objects.all()  # No county filter if none is provided
    
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
                "coordinates": [lon, lat],
                "situation_type": location.filter_used
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
