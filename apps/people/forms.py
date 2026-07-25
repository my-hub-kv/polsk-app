"""Small administrator form for invitation-only participant onboarding."""

from django import forms

from .models import Participant


class ParticipantOnboardingForm(forms.Form):
    display_name = forms.CharField(max_length=120, label="Navn")
    age_group = forms.ChoiceField(
        choices=[
            (Participant.AgeGroup.TODDLER, "0-3 år"),
            (Participant.AgeGroup.CHILD, "4-11 år"),
            (Participant.AgeGroup.TEEN, "12-18 år"),
            (Participant.AgeGroup.ADULT, "Voksen"),
        ],
        label="Aldersgruppe",
    )
    household_name = forms.CharField(max_length=120, label="Husstand")
    create_credentials = forms.BooleanField(
        required=False,
        initial=False,
        label="Opret invitationslink til login",
    )
