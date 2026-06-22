"""
Views for the Instagram Clone.

Class-Based Views are used wherever the work maps cleanly onto Django's
generic views (list/detail/create/update/delete). Lightweight, single
purpose actions (like-toggle, follow-toggle, mark-as-read, AJAX search
suggestions) are implemented as small function-based views guarded by
@login_required, which keeps them simple and readable.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q, Count, Exists, OuterRef
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .forms import CommentForm, DirectMessageForm, LoginForm, PostForm, ProfileForm, StoryForm, UserRegisterForm
from .models import Comment, Conversation, DirectMessage, Follow, Like, Notification, Post, Profile, Story


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
class RegisterView(CreateView):
    """User registration. A Profile is auto-created via signals."""

    model = User
    form_class = UserRegisterForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("feed")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f"Welcome to InstaClone, {self.object.username}!")
        return response

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("feed")
        return super().get(request, *args, **kwargs)


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been logged out.")
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Feed / Explore
# ---------------------------------------------------------------------------
class FeedView(LoginRequiredMixin, ListView):
    """Home feed: posts from people the current user follows, plus their own."""

    model = Post
    template_name = "core/feed.html"
    context_object_name = "posts"
    paginate_by = getattr(settings, "FEED_PER_PAGE", 6)

    def get_queryset(self):
        following_ids = Follow.objects.filter(follower=self.request.user).values_list(
            "following_id", flat=True
        )
        user_filter = Q(user_id__in=following_ids) | Q(user=self.request.user)
        liked_subquery = Like.objects.filter(post=OuterRef("pk"), user=self.request.user)
        return (
            Post.objects.filter(user_filter)
            .select_related("user", "user__profile")
            .prefetch_related("comments__user", "comments__user__profile", "likes")
            .annotate(
                liked_count=Count("likes", distinct=True),
                comment_count=Count("comments", distinct=True),
                user_has_liked=Exists(liked_subquery),
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        following_ids = list(
            Follow.objects.filter(follower=self.request.user).values_list(
                "following_id", flat=True
            )
        )
        story_user_ids = following_ids + [self.request.user.id]
        stories_qs = (
            Story.objects.active()
            .filter(user_id__in=story_user_ids)
            .select_related("user", "user__profile")
            .order_by("user_id", "-created_at")
        )
        # Group active stories by user, preserving "my story" first.
        grouped = {}
        for story in stories_qs:
            grouped.setdefault(story.user_id, []).append(story)
        ordered_user_ids = [self.request.user.id] + [
            uid for uid in following_ids if uid in grouped
        ]
        story_groups = [
            {"user": grouped[uid][0].user, "stories": grouped[uid]}
            for uid in ordered_user_ids
            if uid in grouped
        ]
        context["story_groups"] = story_groups
        context["comment_form"] = CommentForm()
        context["is_feed_empty"] = not context["posts"]
        return context


class ExploreView(LoginRequiredMixin, ListView):
    """Discover posts from everyone, not just people the user follows."""

    model = Post
    template_name = "core/explore.html"
    context_object_name = "posts"
    paginate_by = getattr(settings, "POSTS_PER_PAGE", 9)

    def get_queryset(self):
        liked_subquery = Like.objects.filter(post=OuterRef("pk"), user=self.request.user)
        return (
            Post.objects.exclude(user=self.request.user)
            .select_related("user", "user__profile")
            .prefetch_related("comments")
            .annotate(
                liked_count=Count("likes", distinct=True),
                comment_count=Count("comments", distinct=True),
                user_has_liked=Exists(liked_subquery),
            )
            .order_by("-created_at")
        )


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------
class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = "core/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.select_related("user", "user__profile").prefetch_related(
            "comments__user", "comments__user__profile", "likes"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        context["comments"] = self.object.comments.select_related(
            "user", "user__profile"
        ).order_by("created_at")
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "core/post_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Your post was shared successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("post_detail", kwargs={"pk": self.object.pk})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "core/post_form.html"

    def test_func(self):
        return self.get_object().user_id == self.request.user.id

    def handle_no_permission(self):
        messages.error(self.request, "You can only edit your own posts.")
        return redirect("feed")

    def form_valid(self, form):
        messages.success(self.request, "Your post was updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("post_detail", kwargs={"pk": self.object.pk})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = "core/post_confirm_delete.html"
    success_url = reverse_lazy("feed")

    def test_func(self):
        return self.get_object().user_id == self.request.user.id

    def handle_no_permission(self):
        messages.error(self.request, "You can only delete your own posts.")
        return redirect("feed")

    def form_valid(self, form):
        messages.success(self.request, "Your post was deleted.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------
class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "core/profile_detail.html"
    context_object_name = "profile"
    slug_field = "user__username"
    slug_url_kwarg = "username"

    def get_object(self, queryset=None):
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username)
        profile, _ = Profile.objects.select_related("user").get_or_create(user=user)
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.object.user
        posts = (
            Post.objects.filter(user=profile_user)
            .select_related("user")
            .prefetch_related("likes", "comments")
            .annotate(liked_count=Count("likes", distinct=True))
            .order_by("-created_at")
        )
        paginator_page = self.request.GET.get("page")
        from django.core.paginator import Paginator

        paginator = Paginator(posts, getattr(settings, "POSTS_PER_PAGE", 9))
        context["posts"] = paginator.get_page(paginator_page)
        context["is_own_profile"] = profile_user == self.request.user
        context["is_following"] = (
            not context["is_own_profile"]
            and Follow.objects.filter(
                follower=self.request.user, following=profile_user
            ).exists()
        )
        context["active_stories"] = Story.objects.active().filter(user=profile_user)
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "core/profile_form.html"
    success_url = reverse_lazy("feed")

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, "Your profile was updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("profile_detail", kwargs={"username": self.request.user.username})


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "core/notifications.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "sender", "sender__profile", "post"
        )

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Mark all unread notifications as read once the page is viewed.
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return response


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
class SearchView(LoginRequiredMixin, ListView):
    """Search users by username or profile bio."""

    model = Profile
    template_name = "core/search.html"
    context_object_name = "profiles"
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()
        self.query = query
        if not query:
            return Profile.objects.none()
        return (
            Profile.objects.select_related("user")
            .filter(Q(user__username__icontains=query) | Q(bio__icontains=query))
            .order_by("user__username")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = getattr(self, "query", "")
        return context


@login_required
def search_suggestions(request):
    """AJAX endpoint returning lightweight username/bio search suggestions."""
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        profiles = (
            Profile.objects.select_related("user")
            .filter(Q(user__username__icontains=query) | Q(bio__icontains=query))
            .order_by("user__username")[:8]
        )
        for profile in profiles:
            results.append(
                {
                    "username": profile.user.username,
                    "bio": profile.bio[:60],
                    "url": reverse("profile_detail", kwargs={"username": profile.user.username}),
                    "avatar": profile.profile_picture.url if profile.profile_picture else "",
                }
            )
    return JsonResponse({"results": results})


# ---------------------------------------------------------------------------
# Stories
# ---------------------------------------------------------------------------
class StoryCreateView(LoginRequiredMixin, CreateView):
    model = Story
    form_class = StoryForm
    template_name = "core/story_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Your story was posted! It will expire in 24 hours.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("feed")


class StoryViewerView(LoginRequiredMixin, TemplateView):
    """Slideshow-style viewer for one user's currently-active stories."""

    template_name = "core/story_viewer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get("username")
        story_user = get_object_or_404(User, username=username)
        stories = (
            Story.objects.active().filter(user=story_user).select_related("user", "user__profile")
        )
        if not stories.exists():
            messages.info(self.request, f"{story_user.username} has no active stories right now.")
        context["story_user"] = story_user
        context["stories"] = stories
        return context


@login_required
def story_delete(request, pk):
    story = get_object_or_404(Story, pk=pk)
    if story.user_id != request.user.id:
        messages.error(request, "You can only delete your own stories.")
        return redirect("feed")
    if request.method == "POST":
        story.delete()
        messages.success(request, "Story deleted.")
    return redirect("feed")


# ---------------------------------------------------------------------------
# Likes / Follows / Comments (lightweight action endpoints)
# ---------------------------------------------------------------------------
@login_required
def like_toggle(request, pk):
    """Like a post if not already liked, otherwise unlike it. Prevents duplicates."""
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"liked": liked, "likes_count": post.likes.count()})

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("feed")
    return redirect(next_url)


@login_required
def comment_add(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Comment could not be empty.")
    return redirect("post_detail", pk=post.pk)


@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.user_id != request.user.id and comment.post.user_id != request.user.id:
        return HttpResponseForbidden("You cannot delete this comment.")
    post_pk = comment.post_id
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted.")
    return redirect("post_detail", pk=post_pk)


@login_required
def follow_toggle(request, username):
    """Follow/unfollow a user. Prevents duplicate follows and self-follows."""
    target_user = get_object_or_404(User, username=username)
    if target_user.id == request.user.id:
        messages.error(request, "You cannot follow yourself.")
        return redirect("profile_detail", username=username)

    follow, created = Follow.objects.get_or_create(
        follower=request.user, following=target_user
    )
    if not created:
        follow.delete()
        messages.info(request, f"Unfollowed {target_user.username}.")
    else:
        messages.success(request, f"You are now following {target_user.username}.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "following": created,
                "followers_count": target_user.followers.count(),
            }
        )
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse(
        "profile_detail", kwargs={"username": username}
    )
    return redirect(next_url)


class FollowListView(LoginRequiredMixin, TemplateView):
    """Shows a user's followers or following list depending on `mode`."""

    template_name = "core/follow_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get("username")
        mode = self.kwargs.get("mode")
        profile_user = get_object_or_404(User, username=username)
        if mode == "followers":
            relations = Follow.objects.filter(following=profile_user).select_related(
                "follower", "follower__profile"
            )
            people = [r.follower for r in relations]
        else:
            relations = Follow.objects.filter(follower=profile_user).select_related(
                "following", "following__profile"
            )
            people = [r.following for r in relations]
        context["profile_user"] = profile_user
        context["people"] = people
        context["mode"] = mode
        return context


# ---------------------------------------------------------------------------
# Direct Messages
# ---------------------------------------------------------------------------
class InboxView(LoginRequiredMixin, ListView):
    """Show all conversations for the logged-in user, most recent first."""
    template_name = "core/inbox.html"
    context_object_name = "conversations"

    def get_queryset(self):
        return (
            Conversation.objects.filter(participants=self.request.user)
            .prefetch_related("participants__profile", "messages")
            .order_by("-updated_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversations = context["conversations"]
        enriched = []
        for convo in conversations:
            other = convo.get_other_participant(self.request.user)
            last_msg = convo.get_last_message()
            unread = convo.unread_count_for(self.request.user)
            enriched.append({
                "convo": convo,
                "other": other,
                "last_msg": last_msg,
                "unread": unread,
            })
        context["enriched_conversations"] = enriched
        context["total_unread_dm"] = sum(c["unread"] for c in enriched)
        return context


class ConversationView(LoginRequiredMixin, View):
    """View/send messages in a specific conversation."""

    def get(self, request, pk):
        convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
        convo.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        messages_qs = convo.messages.select_related("sender", "sender__profile").order_by("created_at")
        other = convo.get_other_participant(request.user)
        form = DirectMessageForm()
        all_convos = (Conversation.objects.filter(participants=request.user)
            .prefetch_related("participants__profile", "messages").order_by("-updated_at"))
        enriched = []
        for c in all_convos:
            o = c.get_other_participant(request.user)
            lm = c.get_last_message()
            un = c.unread_count_for(request.user)
            enriched.append({"convo": c, "other": o, "last_msg": lm, "unread": un})
        return render(request, "core/conversation.html", {
            "convo": convo, "messages": messages_qs, "other": other,
            "form": form, "enriched_conversations": enriched,
        })

    def post(self, request, pk):
        convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = convo
            msg.sender = request.user
            msg.save()
            convo.updated_at = msg.created_at
            convo.save(update_fields=["updated_at"])
        return redirect("conversation", pk=pk)


@login_required
def start_conversation(request, username):
    """Start or resume a DM with another user."""
    other_user = get_object_or_404(User, username=username)
    if other_user == request.user:
        messages.error(request, "You cannot message yourself.")
        return redirect("inbox")
    convo, _ = Conversation.get_or_create_between(request.user, other_user)
    return redirect("conversation", pk=convo.pk)


@login_required
def dm_send_ajax(request, pk):
    """AJAX endpoint for sending a message (used by WebSocket fallback)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Empty message"}, status=400)
    msg = DirectMessage.objects.create(
        conversation=convo,
        sender=request.user,
        content=content,
    )
    convo.save(update_fields=["updated_at"])
    return JsonResponse({
        "id": msg.pk,
        "content": msg.content,
        "sender": request.user.username,
        "created_at": msg.created_at.isoformat(),
        "is_read": msg.is_read,
    })


@login_required
def unread_dm_count(request):
    """AJAX: total unread DM count for the current user."""
    count = (
        DirectMessage.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        )
        .exclude(sender=request.user)
        .count()
    )
    return JsonResponse({"count": count})
