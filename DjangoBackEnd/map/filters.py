
import django_filters
from .models import DetectedCollision, VtsSituation # Import VtsSituation if needed for specific lookups/choices, though not strictly necessary here

class DetectedCollisionFilter(django_filters.FilterSet):
    # --- Explicit Filters Targeting Related Model ---

    # Filter by 'severity' field on the related VtsSituation model
    # Using iexact for case-insensitive exact match, suitable for CharField
    severity = django_filters.CharFilter(
        field_name='transit_information__severity',
        lookup_expr='iexact'
    )

    # Filter by 'filter_used' field on the related VtsSituation model
    # Using icontains for case-insensitive substring search, often useful for TextField
    # Or use 'iexact' if you expect exact matches
    filter_used = django_filters.CharFilter(
        field_name='transit_information__filter_used',
        lookup_expr='icontains' # Or 'iexact' if preferred
    )

    # --- Filter for Direct Field on Related Model (Bus Route ID) ---
    # We filter DetectedCollision based on the ID of the related BusRoute
    bus_route = django_filters.CharFilter(
        field_name='bus_route__route_id',   # Filter on the 'route_id' CharField
        lookup_expr='iexact'                # Case-insensitive exact match for route IDs
    )

    # --- Optional: Filter for Direct Field on DetectedCollision ---
    # Example: filter by the boolean field 'published_to_mqtt'
    published = django_filters.BooleanFilter(field_name='published_to_mqtt')


    class Meta:
        model = DetectedCollision
        # List the NAMES of the filters defined ABOVE in this class,
        # or names of fields directly on DetectedCollision if not explicitly defined above.
        fields = [
            'severity',         # Refers to the 'severity' filter defined above
            'filter_used',      # Refers to the 'filter_used' filter defined above
            'bus_route',        # Refers to the 'bus_route' filter defined above
            'published',        # Refers to the 'published' filter defined above
            # You could also add fields directly from DetectedCollision here if you don't need custom lookups:
            # 'detection_timestamp', # Example: would allow filtering like ?detection_timestamp=2024-01-01T12:00:00Z
        ]