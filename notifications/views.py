from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification
from django.shortcuts import render

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    try:
        n = Notification.objects.get(id=notification_id, user=request.user)
        n.is_read = True
        n.save(update_fields=['is_read'])
        return JsonResponse({'status': 'ok'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'msg': 'Not found'}, status=404)


@login_required
@require_POST
def mark_all_read(request):
    updated = Notification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True)
    return JsonResponse({'status': 'ok', 'updated': updated})


@login_required
def all_notifications(request):
    """Full notifications list page for the logged-in user."""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'all_notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })