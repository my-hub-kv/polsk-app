"""Participant-facing validation for the shared event schedule."""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from .models import Activity


class ActivityForm(forms.Form):
    """Validate participant-supplied activity fields without relation lookups."""

    title = forms.CharField(label="Titel", max_length=160)
    description = forms.CharField(
        label="Beskrivelse",
        max_length=2_000,
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    activity_date = forms.DateField(
        label="Dato",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    start_time = forms.TimeField(
        label="Starttidspunkt",
        input_formats=["%H:%M"],
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    )
    end_time = forms.TimeField(
        label="Sluttidspunkt (valgfrit)",
        required=False,
        input_formats=["%H:%M"],
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    )
    is_time_approximate = forms.BooleanField(
        label="Tidspunktet er cirka",
        required=False,
    )

    def __init__(
        self,
        *args: object,
        activity: Activity | None = None,
        **kwargs: object,
    ) -> None:
        """Populate a date-input-compatible initial value when editing an activity."""
        if activity is not None and "initial" not in kwargs:
            kwargs["initial"] = {
                "title": activity.title,
                "description": activity.description,
                "activity_date": activity.activity_date,
                "start_time": activity.start_time,
                "end_time": activity.end_time,
                "is_time_approximate": activity.is_time_approximate,
            }
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, object]:
        """Reject an end time at or before the activity's start time."""
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        if start_time and end_time and end_time <= start_time:
            raise ValidationError("Sluttidspunktet skal ligge efter starttidspunktet.")
        return cleaned_data
