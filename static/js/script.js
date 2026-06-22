/* InstaClone front-end behaviour: AJAX likes/follows + dark mode switch */

(function () {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    function pluralize(count, word) {
        return count + ' ' + word + (count === 1 ? '' : 's');
    }

    // ---- Like toggle (AJAX) -------------------------------------------------
    document.addEventListener('submit', function (e) {
        const form = e.target.closest('.like-form');
        if (!form) return;
        e.preventDefault();

        const postId = form.dataset.postId;
        const url = form.getAttribute('action');

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(new FormData(form)),
        })
            .then((response) => response.json())
            .then((data) => {
                const btn = form.querySelector('.like-btn');
                const icon = btn.querySelector('i');
                if (data.liked) {
                    icon.classList.remove('fa-regular');
                    icon.classList.add('fa-solid', 'text-danger');
                    btn.classList.add('liked', 'like-bump');
                } else {
                    icon.classList.remove('fa-solid', 'text-danger');
                    icon.classList.add('fa-regular');
                    btn.classList.remove('liked');
                    btn.classList.add('like-bump');
                }
                setTimeout(() => btn.classList.remove('like-bump'), 300);

                document
                    .querySelectorAll('.likes-count[data-post-id="' + postId + '"]')
                    .forEach((el) => {
                        el.textContent = pluralize(data.likes_count, 'like');
                    });
            })
            .catch(() => {
                // Fall back to a normal form submission if the AJAX call fails.
                form.submit();
            });
    });

    // ---- Follow toggle (AJAX) -----------------------------------------------
    document.addEventListener('submit', function (e) {
        const form = e.target.closest('#follow-form');
        if (!form) return;
        e.preventDefault();

        const url = form.getAttribute('action');
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(new FormData(form)),
        })
            .then((response) => response.json())
            .then((data) => {
                const btn = form.querySelector('.follow-btn');
                if (data.following) {
                    btn.textContent = 'Following';
                    btn.classList.remove('btn-primary', 'ig-btn');
                    btn.classList.add('btn-outline-secondary');
                } else {
                    btn.textContent = 'Follow';
                    btn.classList.remove('btn-outline-secondary');
                    btn.classList.add('btn-primary', 'ig-btn');
                }
                const followersStat = document.querySelector('.profile-stats a[href*="followers"] strong');
                if (followersStat) {
                    followersStat.textContent = data.followers_count;
                }
            })
            .catch(() => {
                form.submit();
            });
    });

    // ---- Dark mode toggle -----------------------------------------------------
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
    }

    document.addEventListener('DOMContentLoaded', function () {
        const toggle = document.getElementById('darkModeToggle');
        if (toggle) {
            toggle.addEventListener('click', function (e) {
                e.preventDefault();
                const current = document.documentElement.getAttribute('data-bs-theme');
                const next = current === 'dark' ? 'light' : 'dark';
                applyTheme(next);
                const icon = toggle.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-moon', next === 'light');
                    icon.classList.toggle('fa-sun', next === 'dark');
                }
            });
        }

        // Dismiss Bootstrap alerts automatically after a few seconds.
        document.querySelectorAll('.messages-wrap .alert, .messages-wrap-guest .alert').forEach(function (alertEl) {
            setTimeout(function () {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
                bsAlert.close();
            }, 4000);
        });
    });
})();
