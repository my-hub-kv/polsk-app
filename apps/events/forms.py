"""Participant-facing forms for the shared event schedule."""

from django import forms

from .models import Activity


class ActivityForm(forms.ModelForm):
    """Validate the fields a participant may supply for an activity."""

    class Meta:
        model = Activity
        fields = (
            "title",
            "description",
            "activity_date",
            "start_time",
            "end_time",
            "is_time_approximate",
        )
        labels = {
            "title": "Titel",
            "description": "Beskrivelse",
            "activity_date": "Dato",
            "start_time": "Starttidspunkt",
            "end_time": "Sluttidspunkt (valgfrit)",
            "is_time_approximate": "Tidspunktet er cirka",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "activity_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }
