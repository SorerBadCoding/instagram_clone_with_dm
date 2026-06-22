# InstaClone — Instagram Clone (Django)

A full-featured Instagram-style social media application built with Django,
created as a university software engineering / web development project.

## Features

- **Authentication** — registration, login, logout (Django auth + signals auto-create a `Profile` for every new `User`)
- **Posts** — create, edit, delete (owner-only), captions, locations
- **Feed** — posts from people you follow + your own, paginated
- **Explore** — grid of all posts from everyone, paginated
- **Likes** — AJAX like/unlike, duplicate likes prevented at the database level
- **Comments** — add/delete comments on posts
- **Follow system** — follow/unfollow, duplicate follows prevented at the database level, followers/following lists
- **Stories** — 24-hour expiring photo stories with a slideshow viewer; expired stories are hidden automatically
- **Notifications** — follow / like / comment notifications with an unread badge
- **Search** — search users by username or bio, with live AJAX suggestions
- **Profiles** — bio, profile picture, website, location, post/follower/following counts
- **Dark mode** toggle
- **Mobile responsive**, Instagram-style sidebar + bottom navigation
- **Admin panel** — custom configuration with search, filters, and inline profile editing

## Tech Stack

- Python 3 / Django 6
- SQLite (default — zero config)
- Bootstrap 5 + Font Awesome (via CDN)
- Pillow (image handling)

## Project Structure

```
instagram_clone/
├── manage.py
├── requirements.txt
├── config/                 # Project settings, root urls, wsgi/asgi
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                    # Main application
│   ├── models.py            # Profile, Post, Comment, Like, Follow, Story, Notification
│   ├── views.py              # Class-based + function-based views
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   ├── signals.py            # auto-create Profile, auto-create notifications
│   ├── context_processors.py
│   ├── templatetags/
│   │   └── core_extras.py
│   └── migrations/
├── templates/
│   ├── base.html
│   ├── registration/        # login.html, register.html
│   └── core/                # feed, explore, post, profile, search, stories, notifications...
├── static/
│   ├── css/style.css
│   └── js/script.js
└── media/                   # uploaded images (profile pics, posts, stories)
    └── defaults/             # default avatar / post placeholder images
```

## Setup Instructions

1. **Create and activate a virtual environment (recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser** (for the admin panel)

   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**

   ```bash
   python manage.py runserver
   ```

6. Open your browser at **http://127.0.0.1:8000/**
   The admin panel is at **http://127.0.0.1:8000/admin/**

## Notes

- All uploaded media (profile pictures, posts, stories) is stored under `media/`.
  If no profile picture is uploaded, a default avatar (`media/defaults/default_avatar.png`)
  is used automatically.
- Stories automatically expire 24 hours after creation (`STORY_LIFETIME_HOURS` in
  `config/settings.py`) — expired stories are filtered out everywhere by the
  `Story.objects.active()` queryset manager and are never shown in the carousel or viewer.
- Pagination sizes (`POSTS_PER_PAGE`, `FEED_PER_PAGE`) can be tuned in `config/settings.py`.
- This project uses **SQLite** for zero-config local development. To use PostgreSQL/MySQL in
  production, update the `DATABASES` setting in `config/settings.py`.
- `DEBUG` and `SECRET_KEY` are read from environment variables in production
  (`DJANGO_DEBUG`, `DJANGO_SECRET_KEY`) and fall back to safe local-dev defaults otherwise.
  **Do not deploy with the default `SECRET_KEY`.**

## Key Design Decisions

- **Class-Based Views** are used for all standard CRUD/listing operations (`ListView`,
  `DetailView`, `CreateView`, `UpdateView`, `DeleteView`). Lightweight single-purpose
  actions (like-toggle, follow-toggle, AJAX search) are implemented as small
  `@login_required` function views for simplicity and clarity.
- **Signals** (`core/signals.py`) automatically create a `Profile` whenever a `User`
  registers, and automatically create `Notification` records when a `Follow`, `Like`,
  or `Comment` is created.
- **Ownership checks** use `UserPassesTestMixin` (class-based) for post edit/delete, and
  manual checks in function views for comments/stories.
- **Duplicate prevention** is enforced at the database layer with `UniqueConstraint`
  on `Like(user, post)` and `Follow(follower, following)`, in addition to using
  `get_or_create` in the view logic.
- **Query optimization** — `select_related` is used for one-to-one/many-to-one
  relationships (e.g. `post.user`, `post.user.profile`) and `prefetch_related` /
  `annotate` with `Count`/`Exists` subqueries are used for reverse relations
  (likes, comments) to minimize N+1 queries on the feed, explore, and profile pages.
