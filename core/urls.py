"""
URL routes for the core app.
"""

from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    # Feed / Explore
    path("", views.FeedView.as_view(), name="feed"),
    path("explore/", views.ExploreView.as_view(), name="explore"),
    # Posts
    path("post/new/", views.PostCreateView.as_view(), name="post_create"),
    path("post/<int:pk>/", views.PostDetailView.as_view(), name="post_detail"),
    path("post/<int:pk>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("post/<int:pk>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    path("post/<int:pk>/like/", views.like_toggle, name="like_toggle"),
    path("post/<int:pk>/comment/", views.comment_add, name="comment_add"),
    path("comment/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    # Profiles
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("profile/<str:username>/", views.ProfileDetailView.as_view(), name="profile_detail"),
    path(
        "profile/<str:username>/<str:mode>/",
        views.FollowListView.as_view(),
        name="follow_list",
    ),
    path("follow/<str:username>/", views.follow_toggle, name="follow_toggle"),
    # Search
    path("search/", views.SearchView.as_view(), name="search"),
    path("search/suggestions/", views.search_suggestions, name="search_suggestions"),
    # Notifications
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    # Stories
    path("story/new/", views.StoryCreateView.as_view(), name="story_create"),
    path("story/<int:pk>/delete/", views.story_delete, name="story_delete"),
    path("story/<str:username>/", views.StoryViewerView.as_view(), name="story_viewer"),
    # Direct Messages
    path("inbox/", views.InboxView.as_view(), name="inbox"),
    path("inbox/<int:pk>/", views.ConversationView.as_view(), name="conversation"),
    path("inbox/<int:pk>/send/", views.dm_send_ajax, name="dm_send_ajax"),
    path("dm/<str:username>/", views.start_conversation, name="start_conversation"),
    path("api/dm/unread/", views.unread_dm_count, name="unread_dm_count"),
]
