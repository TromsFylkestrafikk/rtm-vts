from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.template import loader
from .models import TransitInformation
from pyproj import CRS, Transformer

def map(request):
    template = loader.get_template('map.html')
    return HttpResponse(template.render())

def location_geojson(request):
    # Query all TransitInformation instances that have latitude and longitude
    locations = TransitInformation.objects.filter(latitude__isnull=False, longitude__isnull=False)

    crs_25833 = CRS('EPSG:25833')
    crs_4326 = CRS('EPSG:4326')

    transformer = Transformer.from_crs(crs_25833, crs_4326)
    
    lon,lat = transformer.transform(269079.634,6567685.167)

    print(lon,lat)

    features = []

    for location in locations:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [location.longitude, location.latitude]  # Using longitude, latitude
            },
            "properties": {
                "name": location.situation_id,  # You can use any field here, like situation_id
                "description": location.location_description  # If you want to add more details in the popup
            }
        })

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    return JsonResponse(geojson_data)