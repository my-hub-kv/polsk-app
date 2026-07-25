"""Forms for invitation-only credential setup."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import PolskUserManager


class PolskAuthenticationForm(AuthenticationForm):
    """Authenticate against Polsk's canonical case-insensitive usernames."""

    def clean_username(self) -> str:
        return PolskUserManager.normalize_username_value(self.cleaned_data["username"])


class InvitationCredentialForm(forms.Form):
    username = forms.CharField(max_length=150, label="Brugernavn")
    email = forms.EmailField(required=False, label="E-mail")
    password = forms.CharField(
        widget=forms.PasswordInput, label="Adgangskode", strip=False
    )
    password_confirmation = forms.CharField(
        widget=forms.PasswordInput, label="Gentag adgangskode", strip=False
    )

    def clean_username(self) -> str:
        return PolskUserManager.normalize_username_value(self.cleaned_data["username"])

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmation = cleaned_data.get("password_confirmation")
        if password and confirmation and password != confirmation:
            self.add_error("password_confirmation", "Adgangskoderne er ikke ens.")
        if password:
            validate_password(password)
        return cleaned_data
