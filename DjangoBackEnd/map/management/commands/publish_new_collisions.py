import time
import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from map.models import DetectedCollision, TransitInformation # Import both

try:
    import paho.mqtt.client as mqtt
    mqtt_available = True
except ImportError:
    mqtt_available = False
    mqtt = None

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks for unpublished collisions and publishes them via MQTT.'

    def _sanitize_topic_segment(self, segment_value, placeholder='_unknown_'):
        """Sanitize a value to be used as an MQTT topic segment."""
        if not segment_value:
            return placeholder
        return str(segment_value).replace('+', '_').replace('#', '_').replace('/', '_')

    def handle(self, *args, **options):
        start_time = time.time()
        if not mqtt_available:
            self.stdout.write(self.style.ERROR("paho-mqtt library not found. Cannot publish."))
            return
        if not mqtt:
            # This case should theoretically not happen if mqtt_available is True, but belts and braces
            self.stdout.write(self.style.ERROR("MQTT client could not be initialized."))
            return

        mqtt_client = None
        base_topic = getattr(settings, 'MQTT_BASE_COLLISION_TOPIC', 'vts/collisions')
        published_count = 0
        processed_count = 0
        successfully_marked_ids = []

        # --- Find Unpublished Collisions ---
        # Important: select_related to avoid N+1 queries later
        collisions_to_publish = DetectedCollision.objects.filter(
            published_to_mqtt=False
        ).select_related('transit_information').order_by('detection_timestamp') # Process oldest first

        processed_count = collisions_to_publish.count()
        if not collisions_to_publish:
            self.stdout.write("No new collisions found to publish.")
            return # Nothing to do

        self.stdout.write(f"Found {processed_count} unpublished collisions. Attempting to publish...")

        # --- Connect to MQTT ---
        try:
            mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            mqtt_client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            mqtt_client.loop_start()
            self.stdout.write(f"Connected to MQTT Broker {settings.MQTT_BROKER_HOST}")
        except Exception as e:
            logger.error(f"Could not connect to MQTT Broker: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f"Could not connect to MQTT Broker: {e}. Aborting publish cycle."))
            return # Don't proceed if connection fails

        # --- Publish Loop ---
        ids_to_mark_published = []
        for collision in collisions_to_publish:
            try:
                # Prepare payload
                payload = {
                     # ... (same payload structure as before) ...
                    "event": "new_collision",
                    "collision_id": collision.id,
                    "transit_id": collision.transit_information_id,
                    "route_id": collision.bus_route_id,
                    "lon": collision.transit_lon,
                    "lat": collision.transit_lat,
                    "tolerance": collision.tolerance_meters,
                    "detected_at": collision.detection_timestamp.isoformat(),
                    "severity": collision.transit_information.severity,
                    "filter_used": collision.transit_information.filter_used,
                    "situation_id": collision.transit_information.situation_id,
                }
                payload_json = json.dumps(payload)

                # Construct topic
                bus_route_id_str = self._sanitize_topic_segment(collision.bus_route_id)
                severity_str = self._sanitize_topic_segment(collision.transit_information.severity)
                filter_str = self._sanitize_topic_segment(collision.transit_information.filter_used)
                topic = f"{base_topic}/route/{bus_route_id_str}/severity/{severity_str}/filter/{filter_str}"

                # Publish
                result = mqtt_client.publish(topic, payload_json)
                result.wait_for_publish(timeout=2.0) # Increase timeout slightly?

                if result.is_published():
                    published_count += 1
                    ids_to_mark_published.append(collision.id) # Add ID to list for bulk update
                    logger.debug(f"Successfully published collision {collision.id} to {topic}")
                else:
                    logger.warning(f"MQTT publish confirmation not received for collision {collision.id}. Will retry on next run.")
                    # DO NOT add to ids_to_mark_published if confirmation fails

            except Exception as pub_e:
                logger.error(f"MQTT publish error for collision {collision.id}: {pub_e}", exc_info=True)
                self.stderr.write(f"MQTT publish error for collision {collision.id}: {pub_e}. Will retry on next run.")
                # DO NOT add to ids_to_mark_published on error

        # --- Mark as Published in DB ---
        if ids_to_mark_published:
            try:
                with transaction.atomic():
                    updated_count = DetectedCollision.objects.filter(
                        id__in=ids_to_mark_published
                    ).update(published_to_mqtt=True)
                successfully_marked_ids = ids_to_mark_published # Assume update worked if no exception
                self.stdout.write(f"Successfully marked {updated_count} collisions as published in the database.")
            except Exception as db_e:
                 logger.error(f"Failed to mark collisions as published in database: {db_e}", exc_info=True)
                 self.stderr.write(self.style.ERROR(f"Failed to mark collisions as published: {db_e}"))
                 # Note: These items might be republished on the next run if the DB update failed

        # --- Cleanup MQTT ---
        if mqtt_client:
            try:
                mqtt_client.loop_stop()
                mqtt_client.disconnect()
                self.stdout.write("Disconnected from MQTT Broker.")
            except Exception as e:
                 logger.warning(f"Error during MQTT disconnect: {e}")

        end_time = time.time()
        self.stdout.write(self.style.SUCCESS(
            f"Publish cycle finished in {end_time - start_time:.2f} seconds. "
            f"Processed: {processed_count}. Published: {published_count}. Marked as published: {len(successfully_marked_ids)}."
        ))