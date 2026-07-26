# User experience

Participant screens are mobile-first, calm, Danish, and family-oriented. The agenda is home: today is highlighted, opening positions near today, and “Gå til i dag” is available. Mine, Household, and All filters; a day-responsible header; simple chore cards; full-team details; and a separate all-chores screen make responsibilities clear.

Show an obvious switched-profile banner. Keep notifications low-volume, omit chore done buttons and message seen requirements, and avoid unnecessary confirmation prompts. Opening the notification center may clear its unread badge without creating message read receipts. Administrative screens may be desktop-oriented. Design loading, empty, error, offline, and permission-denied states; never rely on colour alone.

Suggested labels, not final branding: **Agenda**, **Opgaver**, **Beskeder**, **Mad og indkøb**, **Mere**; **Mine**, **Husstanden**, **Alle**, **I dag**, **Gå til i dag**, **Dagsansvarlig**, **Opgaveansvarlig**, **Børnemadansvarlig**.

Use the supplied campfire mark as the Polsk logo. The shared interface has an accessible, blue-led light and dark theme with a warm orange accent, uses the browser colour preference by default, and offers a presentation-only user choice. The theme must use text, icons, or borders in addition to colour to communicate state. Ordinary administration belongs in the same role-aware UI; Django Admin remains an unlinked emergency backend.

In the native app, Starti provides safe-area inset values and the shared shell applies them to the header, login screen, content, and mobile navigation. The native top and bottom safe areas follow the selected presentation theme: light uses a light background with dark system text and icons, while dark uses dark blue-grey with light system text and icons. This updates immediately when the participant changes theme.

When the Starti bridge reports that the page is running in the native app, authenticated participant pages show a small, non-fixed two-line orange “Powered by starti.app” pill after the page content. It remains hidden in a normal browser, links to Starti.app, and stays outside the primary navigation and fixed mobile navigation.
