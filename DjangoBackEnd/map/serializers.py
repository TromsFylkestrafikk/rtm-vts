
from rest_framework import serializers
from .models import DetectedCollision, BusRoute, VtsSituation

# Simple serializers
class BusRouteSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusRoute
        fields = ['id', 'route_id']

class VtsSituationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VtsSituation
        fields = ['id', 'filter_used', 'severity']


# Main serializer for DetectedCollision
class DetectedCollisionSerializer(serializers.ModelSerializer):
    bus_route = BusRouteSimpleSerializer(read_only=True)
    transit_information = VtsSituationSimpleSerializer(read_only=True)

    class Meta:
        model = DetectedCollision
        # List ONLY fields that should go in the 'properties' section.
        # DO NOT include the geo_field ('collision_point') here.
        fields = [
            'id',
            'bus_route',            # Nested serializer output
            'transit_information',  # Nested serializer output
            'detection_timestamp',
            'transit_lon',          # Keep original coords if useful
            'transit_lat',          # Keep original coords if useful
            'published_to_mqtt',
            'tolerance_meters',
            # Add any other NON-GEOMETRY fields from DetectedCollision
        ]