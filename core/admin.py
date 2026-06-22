"""
Custom Django admin configuration for the Instagram Clone.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User

from .models import Comment, Follow, Like, Notification, Post, Profile, Story


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class UserAdmin(DefaultUserAdmin):
    """Extend the default User admin to show the inline Profile and allow
    searching by username/email."""

    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_staff", "is_active", "is_superuser")


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "followers_count", "following_count", "posts_count", "created_at")
    search_fields = ("user__username", "user__email", "bio", "location")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "short_caption", "likes_count", "comments_count", "created_at")
    search_fields = ("user__username", "caption", "location")
    list_filter = ("created_at", "location")
    autocomplete_fields = ["user"]
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    @admin.display(description="Caption")
    def short_caption(self, obj):
        return (obj.caption[:50] + "...") if len(obj.caption) > 50 else obj.caption


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "short_content", "created_at")
    search_fields = ("user__username", "content")
    list_filter = ("created_at",)
    autocomplete_fields = ["user", "post"]

    @admin.display(description="Content")
    def short_content(self, obj):
        return (obj.content[:50] + "...") if len(obj.content) > 50 else obj.content


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "created_at")
    search_fields = ("user__username",)
    list_filter = ("created_at",)
    autocomplete_fields = ["user", "post"]


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
    list_filter = ("created_at",)
    autocomplete_fields = ["follower", "following"]


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "expires_at", "is_active_display")
    search_fields = ("user__username", "caption")
    list_filter = ("created_at",)
    autocomplete_fields = ["user"]

    @admin.display(description="Active?", boolean=True)
    def is_active_display(self, obj):
        return obj.is_active


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "sender", "notification_type", "is_read", "created_at")
    search_fields = ("recipient__username", "sender__username")
    list_filter = ("notification_type", "is_read", "created_at")
    autocomplete_fields = ["recipient", "sender", "post"]


admin.site.site_header = "InstaClone Administration"
admin.site.site_title = "InstaClone Admin"
admin.site.index_title = "Manage Users, Posts, Stories & Notifications"


# ── NEW: Direct Messages ──────────────────────────────────────────────────
from .models import Conversation, DirectMessage  # noqa: E402


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "participant_list", "created_at", "updated_at")
    search_fields = ("participants__username",)
    filter_horizontal = ("participants",)

    @admin.display(description="Participants")
    def participant_list(self, obj):
        return ", ".join(u.username for u in obj.participants.all())


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "conversation", "short_content", "is_read", "created_at")
    search_fields = ("sender__username", "content")
    list_filter = ("is_read", "created_at")
    autocomplete_fields = ["sender"]

    @admin.display(description="Content")
    def short_content(self, obj):
        return (obj.content[:60] + "...") if len(obj.content) > 60 else obj.content
