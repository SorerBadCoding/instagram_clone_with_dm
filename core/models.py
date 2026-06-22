"""
Database models for the Instagram Clone.

Relationships
-------------
Profile      -> OneToOne with User
Post         -> ForeignKey User
Comment      -> ForeignKey User, ForeignKey Post
Like         -> ForeignKey User, ForeignKey Post (unique together)
Follow       -> follower User, following User (unique together)
Story        -> ForeignKey User, image, created_at, expires_at
Notification -> recipient, sender, notification_type, created_at, is_read
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


User = settings.AUTH_USER_MODEL


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
class Profile(models.Model):
    """Extra information attached to every Django User (1-to-1)."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        default="defaults/default_avatar.png",
        blank=True,
    )
    website = models.URLField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_absolute_url(self):
        return reverse("profile_detail", kwargs={"username": self.user.username})

    @property
    def followers_count(self):
        return self.user.followers.count()

    @property
    def following_count(self):
        return self.user.following.count()

    @property
    def posts_count(self):
        return self.user.posts.count()


# ---------------------------------------------------------------------------
# Post
# ---------------------------------------------------------------------------
class Post(models.Model):
    """A single photo post created by a user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to="posts/")
    caption = models.TextField(max_length=2200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self):
        return f"Post #{self.pk} by {self.user.username}"

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"pk": self.pk})

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()

    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------
class Comment(models.Model):
    """A comment left by a user on a post."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on Post #{self.post_id}"


# ---------------------------------------------------------------------------
# Like
# ---------------------------------------------------------------------------
class Like(models.Model):
    """A 'like' by a user on a post. A user can only like a post once."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_like_per_user_post")
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} likes Post #{self.post_id}"


# ---------------------------------------------------------------------------
# Follow
# ---------------------------------------------------------------------------
class Follow(models.Model):
    """A 'follow' relationship between two users."""

    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="unique_follow_per_pair"
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.follower_id == self.following_id:
            raise ValidationError("Users cannot follow themselves.")


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------
def default_story_expiry():
    hours = getattr(settings, "STORY_LIFETIME_HOURS", 24)
    return timezone.now() + timedelta(hours=hours)


class StoryQuerySet(models.QuerySet):
    def active(self):
        """Only stories that have not yet expired."""
        return self.filter(expires_at__gt=timezone.now())


class Story(models.Model):
    """A temporary (24h) photo update from a user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stories")
    image = models.ImageField(upload_to="stories/")
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_story_expiry)

    objects = StoryQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Story #{self.pk} by {self.user.username}"

    @property
    def is_active(self):
        return self.expires_at > timezone.now()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = default_story_expiry()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------
class Notification(models.Model):
    """An in-app notification sent to a user (follow / like / comment)."""

    class NotificationType(models.TextChoices):
        FOLLOW = "follow", "Follow"
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_notifications"
    )
    notification_type = models.CharField(max_length=10, choices=NotificationType.choices)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.notification_type}"

    def get_text(self):
        mapping = {
            self.NotificationType.FOLLOW: "started following you.",
            self.NotificationType.LIKE: "liked your post.",
            self.NotificationType.COMMENT: "commented on your post.",
        }
        return mapping.get(self.notification_type, "")


# ---------------------------------------------------------------------------
# Direct Messages
# ---------------------------------------------------------------------------
class Conversation(models.Model):
    """A conversation thread between exactly two users."""

    participants = models.ManyToManyField(User, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation #{self.pk}"

    def get_other_participant(self, user):
        return self.participants.exclude(pk=user.pk).select_related("profile").first()

    def get_last_message(self):
        return self.messages.order_by("-created_at").first()

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    @classmethod
    def get_or_create_between(cls, user1, user2):
        """Return an existing conversation between two users or create one."""
        existing = (
            cls.objects.filter(participants=user1)
            .filter(participants=user2)
            .distinct()
            .first()
        )
        if existing:
            return existing, False
        convo = cls.objects.create()
        convo.participants.add(user1, user2)
        return convo, True


class DirectMessage(models.Model):
    """A single message sent within a Conversation."""

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["conversation", "created_at"])]

    def __str__(self):
        return f"DM #{self.pk} from {self.sender.username} in Convo #{self.conversation_id}"
