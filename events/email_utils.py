from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def _send(subject, template, context, recipient_email):
    """Internal helper — renders HTML template, strips for plain text, sends."""
    html_content = render_to_string(template, context)
    text_content = strip_tags(html_content)
    send_mail(
        subject=subject,
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        html_message=html_content,
        fail_silently=True,
    )


def send_registration_email(user, event):
    _send(
        subject=f"You're Registered — {event.title}",
        template="emails/registration_confirmed.html",
        context={"user": user, "event": event},
        recipient_email=user.email,
    )


def send_pass_active_email(user, event, pass_code):
    _send(
        subject=f"Your Pass Is Ready — {event.title}",
        template="emails/pass_active.html",
        context={"user": user, "event": event, "pass_code": pass_code},
        recipient_email=user.email,
    )


def send_cancellation_email(user, event):
    _send(
        subject=f"Event Cancelled — {event.title}",
        template="emails/event_cancelled.html",
        context={"user": user, "event": event},
        recipient_email=user.email,
    )


def send_event_rejection_email(user, event, reason):
    _send(
        subject=f"Event Proposal Not Approved — {event.title}",
        template="emails/event_rejected.html",
        context={"user": user, "event": event, "reason": reason},
        recipient_email=user.email,
    )


def send_event_approval_email(user, event):
    _send(
        subject=f"Event Approved — {event.title}",
        template="emails/event_approved.html",
        context={"user": user, "event": event},
        recipient_email=user.email,
    )