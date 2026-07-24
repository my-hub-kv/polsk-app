# Conceptual data model

**Status: Candidate design. Implementation: Planned.**

This is non-binding; final fields and relationships require a feature specification and migration review.

**Account-model prerequisite: Candidate decision.** Before account-domain implementation begins, decide and record whether the default Django user model is sufficient. Do not change user-model strategy implicitly after identity data or dependent migrations exist.

- **Accounts/people:** User/LoginAccount, Participant, Household, HouseholdMembership, EventParticipation, EventRole, Invitation, active-profile session context.
- **Events/schedule:** EventSeries, EventYear, venue/location fields, Activity, ActivityAudience, Reminder.
- **Chores:** ChoreType, ChoreOccurrence, ChorePlanVersion, ChoreAssignment, ParticipantChoreSettings, ParticipantDailyAvailability, ChorePreference, ChoreTransferRequest.
- **Communication:** Channel, ChannelMembership, ChannelSubscription, Message, optional later attachment.
- **Food/shopping:** Product, ProductUnit, StorageLocation, StockObservation, MissingReport, FoodReservation, DinnerBox/NamedPurpose, ShoppingRequest, ShoppingList, ShoppingListLine, ShoppingExport, optional VendorProductReference.
- **Weather:** WeatherLocation, ForecastSnapshot, DailyForecast, ObservedWeather.
- **Notification/audit:** Notification, NotificationDelivery, NotificationPreference, PushSubscription, OutboxEntry, AuditEvent.
