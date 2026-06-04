from .models import Notification

def create_notification(role, title, message, user=None, event=None):
    """
    role   : 'STUDENT' | 'TEACHER' | 'ADMIN'
    user   : specific User (None = broadcast to role)
    event  : Event FK for deep-linking (optional)
    """
    Notification.objects.create(
        role=role,
        title=title,
        message=message,
        user=user,
        event=event,
    )