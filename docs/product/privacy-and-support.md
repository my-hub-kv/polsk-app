# Privacy and support

**Public information pages: Implemented. Automated account deletion: Planned.**

The public, login-free pages `web/privatlivspolitik/` and `web/kontakt/` provide
the mobile-store privacy-policy and support URLs. They are linked from the login
screen and authenticated account menu so the privacy policy is also accessible
inside the app.

`web/kontakt/#slet-konto` is the current external and in-app initiation route
for account-deletion requests. It uses the approved support email and promises a
manual response within seven days. It does not perform an automated server-side
deletion; the completed deletion workflow remains planned and must preserve
shared event history while removing or anonymising personal data as described in
[deletion and history](../domain/deletion-and-history.md).

Before any mobile-store submission or change to native provider features,
confirm Starti.app's processor terms, subprocessors, data locations, and enabled
analytics modules. Update the public policy and the Apple App Privacy/Google
Play Data safety declarations before enabling any new data processing.
