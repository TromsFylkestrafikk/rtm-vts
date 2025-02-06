from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.template import loader
from .models import TransitInformation
from pyproj import CRS, Transformer
import ast  # Safe alternative to eval() for string-to-list conversion

def map(request):
    template = loader.get_template('map.html')
    return HttpResponse(template.render())

cords = [
    (269079.634, 6567685.167), (269081.104, 6567685.078), (269085.103, 6567685.261),
    (269131.59, 6567689.679), (269193.36, 6567696.577), (269213.023, 6567699.217),
    (269252.924, 6567704.036), (269290.051, 6567708.172), (269322.884, 6567710.865),
    (269350.248, 6567713.464), (269520.105, 6567732.553), (269542.326, 6567735.039),
    (269549.533, 6567735.88)
]
# def location_geojson(request):
#     # Query all TransitInformation instances that have latitude and longitude

#     crs_25833 = CRS('EPSG:25833')
#     crs_4326 = CRS('EPSG:4326')

#     transformer = Transformer.from_crs(crs_25833, crs_4326)
#     transformed_coords = []
    
#     for coords in cords:
#         lon, lat = transformer.transform(coords[0], coords[1])  
#         #this is flipped, idk why, the map reads it wrong if i pass it the actual way to order it
#         transformed_coords.append([lat,lon])  

#     locations = TransitInformation.objects.filter(latitude__isnull=False, longitude__isnull=False)


#     features = []
    
#     line_feature = {
#         "type": "Feature",
#         "geometry": {
#             "type": "LineString",
#             "coordinates": transformed_coords  # The list of transformed coordinates forms the line
#         },
#         "properties": {
#             "name": "Custom Line",  # Optional, you can name your line or add other properties
#             "description": "A custom line based on coordinates"  # Optional description
#         }
#     }
    
#     features.append(line_feature)

#     for location in locations:
#         features.append({
#             "type": "Feature",
#             "geometry": {
#                 "type": "Point",
#                 "coordinates": [location.longitude, location.latitude]  # Using longitude, latitude
#             },
#             "properties": {
#                 "name": location.situation_id,  # You can use any field here, like situation_id
#                 "description": location.location_description  # If you want to add more details in the popup
#             }
#         })

#     geojson_data = {
#         "type": "FeatureCollection",
#         "features": features
#     }

#     return JsonResponse(geojson_data)

def is_epsg_4326(lon, lat):
    """ Check if coordinates are already in EPSG:4326 (lat/lon) format. """
    return -180 <= lon <= 180 and -90 <= lat <= 90
def location_geojson(request):
    crs_25833 = CRS('EPSG:25833')
    crs_4326 = CRS('EPSG:4326')
    transformer = Transformer.from_crs(crs_25833, crs_4326, always_xy=True)

    locations = TransitInformation.objects.all()
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
                "name": location.situation_id,
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
                    "name": location.situation_id,
                    "description": location.location_description
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
                            "name": location.situation_id,
                            "description": location.location_description
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


# def location_geojson(request):
#     crs_25833 = CRS('EPSG:25833')
#     crs_4326 = CRS('EPSG:4326')

#     transformer = Transformer.from_crs(crs_25833, crs_4326)
#     transformed_coords = []

#     for coords in cords:
#         lon, lat = transformer.transform(coords[0], coords[1])  # Ensure correct order
#         transformed_coords.append([lat, lon])

#     locations = TransitInformation.objects.filter(latitude__isnull=False, longitude__isnull=False)

#     features = []

#     line_feature = {
#         "type": "Feature",
#         "geometry": {
#             "type": "LineString",
#             "coordinates": transformed_coords
#         },
#         "properties": {
#             "name": "Custom Line",
#             "description": "A custom line based on coordinates"
#         }
#     }

#     features.append(line_feature)

#     transit_list = []
#     for location in locations:
#         transit_list.append({
#             "id": location.id,
#             "name": location.situation_id,
#             "description": location.location_description,
#             "coordinates": [location.longitude, location.latitude]
#         })

#         features.append({
#             "type": "Feature",
#             "geometry": {
#                 "type": "Point",
#                 "coordinates": [location.longitude, location.latitude]
#             },
#             "properties": {
#                 "name": location.situation_id,
#                 "description": location.location_description
#             }
#         })

#     geojson_data = {
#         "type": "FeatureCollection",
#         "features": features,
#         "transit_list": transit_list  # Send a separate list of transit entries
#     }

#     return JsonResponse(geojson_data)
