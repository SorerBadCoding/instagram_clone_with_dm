"""
Forms used across the Instagram Clone app.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, Post, Comment, Story


BOOTSTRAP_TEXT = {"class": "form-control"}


class LoginForm(AuthenticationForm):
    """Login form styled with Bootstrap classes."""

    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username", "autofocus": True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )


class UserRegisterForm(UserCreationForm):
    """Registration form: username, email, password1, password2."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm password"}
        )
        for field in self.fields.values():
            field.help_text = None

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    """Edit profile: bio, picture, website, location + first/last name & email."""

    first_name = forms.CharField(
        max_length=150, required=False, widget=forms.TextInput(attrs=BOOTSTRAP_TEXT)
    )
    last_name = forms.CharField(
        max_length=150, required=False, widget=forms.TextInput(attrs=BOOTSTRAP_TEXT)
    )
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs=BOOTSTRAP_TEXT))

    class Meta:
        model = Profile
        fields = ["profile_picture", "bio", "website", "location"]
        widgets = {
            "profile_picture": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Tell people about yourself"}
            ),
            "website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://example.com"}
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Location"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user_id:
            user = self.instance.user
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            profile.save()
        return profile


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["image", "caption", "location"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "caption": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Write a caption...",
                }
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Add location"}
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Add a comment...",
                    "autocomplete": "off",
                }
            )
        }


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ["image", "caption"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "caption": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Add a caption (optional)"}
            ),
        }


class DirectMessageForm(forms.ModelForm):
    """Form for composing a direct message."""

    class Meta:
        from .models import DirectMessage
        model = DirectMessage
        fields = ["content"]
        widgets = {
            "content": forms.TextInput(
                attrs={
                    "class": "form-control dm-input",
                    "placeholder": "Message...",
                    "autocomplete": "off",
                    "id": "dm-message-input",
                }
            )
        }
