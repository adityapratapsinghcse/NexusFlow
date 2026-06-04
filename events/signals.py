import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from .models import EventRegistration
from notifications.utils import create_notification
from django.db.models import Q

logger = logging.getLogger(__name__)


@receiver(post_save, sender='events.Event')
def create_event_notifications(sender, instance, **kwargs):
    logger.debug("Signal: Event '%s' saved with status '%s'", instance.title, instance.status)
    
    Notification = apps.get_model('notifications', 'Notification')
    
    if instance.status == "APPROVED":
        Notification.objects.get_or_create(
            role='STUDENT',
            title=f"New Event: {instance.title}",
            defaults={
                'message': f"Event '{instance.title}' is now approved!",
                'is_read': False
            }
        )

@receiver(post_save, sender=EventRegistration)
def check_event_full(sender, instance, **kwargs):
    event = instance.event
    registered_count = EventRegistration.objects.filter(event=event).count()
    
    # If full, notify the teacher/admin
    if registered_count >= event.expected_crowd:
        create_notification(
            role='TEACHER',
            user=event.organizer,
            title='Event Full',
            message=f"'{event.title}' has reached its expected crowd. Registration closed."
        )
