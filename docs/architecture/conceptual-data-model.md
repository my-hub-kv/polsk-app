# Conceptual data model

**Status: Candidate design. Implementation: Foundation implemented.**

This is non-binding; final fields and relationships require a feature specification and migration review.

**Account-model decision: Implemented.** `accounts.User` subclasses Django's `AbstractUser`, retains username/password login, adds a public UUID, and remains distinct from `Participant`.

- **Accounts/people:** User/LoginAccount, Participant, Household, HouseholdMembership, EventParticipation, EventRole, Invitation, active-profile session context.
- **Events/schedule:** EventSeries, EventYear, venue/location fields, Activity, ActivityAudience, Reminder.
- **Chores:** ChoreType, ChoreOccurrence, ChorePlanVersion, ChoreAssignment, ParticipantChoreSettings, ParticipantDailyAvailability, ChorePreference, ChoreTransferRequest.
- **Communication:** Channel, ChannelMembership, ChannelSubscription, Message, optional later attachment.
- **Food/shopping:** Product, ProductUnit, StorageLocation, StockObservation, MissingReport, FoodReservation, DinnerBox/NamedPurpose, ShoppingRequest, ShoppingList, ShoppingListLine, ShoppingExport, optional VendorProductReference.
- **Weather:** WeatherLocation, ForecastSnapshot, DailyForecast, ObservedWeather.
- **Notification:** Notification, NotificationDelivery, and per-account notification state. There is no generic audit model or stored push token.
