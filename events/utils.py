import random
import string
from django.core.files.base import ContentFile
from django.db import IntegrityError
from io import BytesIO
import qrcode
from .models import EventRegistration
from .email_utils import send_registration_email


def generate_unique_pass(registration, length=10, max_attempts=10):
    """Generates a collision-safe unique pass code with retry logic."""
    if registration.unique_pass:
        return
    from .models import EventRegistration
    for _ in range(max_attempts):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not EventRegistration.objects.filter(unique_pass=code).exists():
            registration.unique_pass = code
            registration.save(update_fields=['unique_pass'])
            return
    raise ValueError(f"Could not generate unique pass after {max_attempts} attempts.")

def generate_qr_code(registration):
    qr_data = f"""
    Event: {registration.event.title}
    Student: {registration.student.get_full_name()}
    Pass: {registration.unique_pass}
    """
    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    filename = f'qr_{registration.id}.png'
    registration.qr_code_image.save(filename,ContentFile(buffer.getvalue()),save=True)
    
def promote_from_waitlist(event):
    """Call this after any registration cancellation to offer the spot."""
    from .models import WaitlistEntry, EventRegistration
    from notifications.utils import create_notification

    current_count = EventRegistration.objects.filter(event=event).count()
    if current_count >= event.expected_crowd:
        return  # still full

    next_entry = WaitlistEntry.objects.filter(event=event).first()
    if not next_entry:
        return  # waitlist empty

    # Promote — create the actual registration
    reg = EventRegistration.objects.create(
        student=next_entry.student,
        event=event,
        verified=False,
        pass_active=False
    )
    from .utils import generate_qr_code, generate_unique_pass
    generate_unique_pass(reg)
    generate_qr_code(reg)
    send_registration_email(next_entry.student, event)
    next_entry.delete()

    create_notification(
        role='STUDENT',
        user=next_entry.student,
        title='Waitlist: spot available!',
        message=f"A spot opened up for '{event.title}'. You're now registered!"
    )
