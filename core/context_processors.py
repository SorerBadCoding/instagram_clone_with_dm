"""
Custom context processors made available to every template.
"""

from .models import Notification, DirectMessage


def notifications_context(request):
    """
    Adds unread notification count, navbar notifications,
    and unread DM count to every template context.
    """
    if request.user.is_authenticated:
        qs = Notification.objects.filter(recipient=request.user).select_related(
            "sender", "sender__profile", "post"
        )
        unread_dm = (
            DirectMessage.objects.filter(
                conversation__participants=request.user,
                is_read=False,
            )
            .exclude(sender=request.user)
            .count()
        )
        return {
            "unread_notifications_count": qs.filter(is_read=False).count(),
            "navbar_notifications": qs[:5],
            "unread_dm_count": unread_dm,
        }
    return {
        "unread_notifications_count": 0,
        "navbar_notifications": [],
        "unread_dm_count": 0,
    }
