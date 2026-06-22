"""
Custom template tags and filters for the Instagram Clone.
"""

from django import template
from django.db.models import QuerySet

from core.models import Follow, Like

register = template.Library()


@register.simple_tag
def is_following(user, target_user):
    """Return True if `user` follows `target_user`."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not target_user or user.pk == getattr(target_user, "pk", None):
        return False
    return Follow.objects.filter(follower=user, following=target_user).exists()


@register.simple_tag
def has_liked(post, user):
    """Return True if `user` has liked `post`."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return Like.objects.filter(post=post, user=user).exists()


@register.filter
def get_item(dictionary, key):
    """Generic dict lookup filter: {{ mydict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def truncate_chars(value, length=60):
    """Truncate a string to `length` characters, appending an ellipsis."""
    if value is None:
        return ""
    value = str(value)
    if len(value) <= length:
        return value
    return value[: length - 1].rstrip() + "\u2026"


@register.filter
def is_queryset_empty(value):
    if isinstance(value, QuerySet):
        return not value.exists()
    return not bool(value)
