import time
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from map.models import DetectedCollision # Import the new storage model
from map.utils import calculate_collisions_for_storage # Import the calculation function

class Command(BaseCommand):
    help = 'Recalculates and updates the stored detected collisions between VTS points and bus routes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tolerance',
            type=int,
            default=50, # Default tolerance if not specified
            help='Distance tolerance in meters for collision detection.',
        )
        parser.add_argument(
            '--no-clear',
            action='store_true',
            help='Do not clear existing collision data before inserting new data (use with caution).',
        )

    @transaction.atomic # Ensure clearing and inserting happen together or not at all
    def handle(self, *args, **options):
        tolerance = options['tolerance']
        clear_existing = not options['no_clear']
        start_time = time.time()

        self.stdout.write(f"Starting collision update process with tolerance {tolerance}m...")

        # --- Calculate New Collisions ---
        # This is the potentially slow part
        calculated_data = calculate_collisions_for_storage(tolerance)
        if not isinstance(calculated_data, list):
             raise CommandError("Collision calculation function did not return a list.")

        calculation_time = time.time()
        self.stdout.write(f"Calculation finished in {calculation_time - start_time:.2f} seconds. Found {len(calculated_data)} potential collisions.")

        # --- Clear Old Data (Optional but Recommended for Refresh) ---
        if clear_existing:
            self.stdout.write("Clearing existing collision data...")
            deleted_count, _ = DetectedCollision.objects.all().delete()
            self.stdout.write(f"Deleted {deleted_count} old collision records.")
        else:
            self.stdout.write(self.style.WARNING("Skipping clearing of existing data (--no-clear specified)."))


        # --- Store New Collision Data ---
        self.stdout.write("Storing new collision data...")
        collisions_to_create = []
        created_count = 0
        skipped_count = 0 # Count duplicates if not clearing

        # Use a set to track pairs already added in this run if not clearing
        # to avoid violating unique_together constraint if duplicates exist in calculated_data
        seen_pairs = set()

        for data in calculated_data:
            pair = (data['transit_id'], data['route_id'])
            if not clear_existing and pair in seen_pairs:
                 skipped_count +=1
                 continue

            collisions_to_create.append(
                DetectedCollision(
                    transit_information_id=data['transit_id'],
                    bus_route_id=data['route_id'],
                    transit_lon=data['transit_lon'],
                    transit_lat=data['transit_lat'],
                    tolerance_meters=tolerance
                )
            )
            if not clear_existing:
                seen_pairs.add(pair)


        # Use bulk_create for much faster insertion
        if collisions_to_create:
            try:
                created_objects = DetectedCollision.objects.bulk_create(collisions_to_create)
                created_count = len(created_objects)
            except Exception as e: # Catch potential integrity errors if unique_together violated
                self.stderr.write(self.style.ERROR(f"Error during bulk create (potentially duplicate pairs?): {e}"))
                self.stdout.write(self.style.WARNING("Attempting insert one-by-one to isolate issue (slower)..."))
                created_count = 0
                # Fallback to individual creates if bulk fails (much slower)
                seen_pairs_individual = set() # Need separate tracking if not clearing
                for data in calculated_data:
                    pair = (data['transit_id'], data['route_id'])
                    if not clear_existing and pair in seen_pairs_individual: continue
                    try:
                         obj, created = DetectedCollision.objects.get_or_create(
                              transit_information_id=data['transit_id'],
                              bus_route_id=data['route_id'],
                              defaults={
                                    'transit_lon': data['transit_lon'],
                                    'transit_lat': data['transit_lat'],
                                    'tolerance_meters': tolerance
                              }
                         )
                         if created:
                            created_count += 1
                         seen_pairs_individual.add(pair)
                    except Exception as e_ind:
                         self.stderr.write(f"Skipping pair {pair} due to error: {e_ind}")


        end_time = time.time()
        self.stdout.write(self.style.SUCCESS(
            f"Collision update finished in {end_time - start_time:.2f} seconds. "
            f"Stored: {created_count}. Skipped duplicates (if not clearing): {skipped_count}."
        ))