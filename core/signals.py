"""
Signal handlers.

* Automatically create a Profile whenever a new User is registered.
* Automatically create a Notification when a Follow / Like / Comment happens.
"""

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Profile, Follow, Like, Comment, Notification


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile automatically whenever a User registers."""
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Make sure the profile is saved/exists whenever the user is saved."""
    Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created and instance.follower_id != instance.following_id:
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.follower,
            notification_type=Notification.NotificationType.FOLLOW,
        )


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if created and instance.user_id != instance.post.user_id:
        Notification.objects.create(
            recipient=instance.post.user,
            sender=instance.user,
            notification_type=Notification.NotificationType.LIKE,
            post=instance.post,
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.user_id != instance.post.user_id:
        Notification.objects.create(
            recipient=instance.post.user,
            sender=instance.user,
            notification_type=Notification.NotificationType.COMMENT,
            post=instance.post,
        )
