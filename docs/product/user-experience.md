# User experience

Participant screens are mobile-first, calm, Danish, and family-oriented. The agenda is home: today is highlighted, opening positions near today, and “Gå til i dag” is available. Mine, Household, and All filters; a day-responsible header; simple chore cards; full-team details; and a separate all-chores screen make responsibilities clear.

Show an obvious switched-profile banner. Keep notifications low-volume, omit chore done buttons and message seen requirements, and avoid unnecessary confirmation prompts. Opening the notification center may clear its unread badge without creating message read receipts. Administrative screens may be desktop-oriented. Design loading, empty, error, offline, and permission-denied states; never rely on colour alone.

Suggested labels, not final branding: **Agenda**, **Opgaver**, **Beskeder**, **Mad**, **Mere**; **Indkøb** is available under **Mere**; **Mine**, **Husstanden**, **Alle**, **I dag**, **Gå til i dag**, **Dagsansvarlig**, **Opgaveansvarlig**, **Børnemadansvarlig**.

The participant release surface is defined in a versioned code registry. The initial published navigation contains **Agenda** and **Mere**; **Mere** contains **Deltagere** and **Notifikationer**. A published page may have an honest empty state: Agenda says “Der er endnu ingen aktiviteter i programmet.” until activities are added. Staff users may review unpublished participant pages, while ordinary participants are redirected to Agenda. This release visibility is not authorization and never grants access to a feature action or administrator operation.

Use the supplied campfire mark as the Polsk logo. The shared interface has an accessible, blue-led light and dark theme with a warm orange accent, uses the browser colour preference by default, and offers a presentation-only user choice. The theme must use text, icons, or borders in addition to colour to communicate state. Ordinary administration belongs in the same role-aware UI; Django Admin remains an unlinked emergency backend.

The participant shell is mobile-first and app-like: mobile content uses the full screen width without an outer card or gutter; the fixed bottom navigation respects the device safe area and immediately marks a newly selected destination while the server-rendered page loads. The sticky header sits above the navigation, and the account control opens a full-screen mobile menu above both. On desktop, primary navigation remains a pill row and account controls use a compact menu. These layers use deliberate stacking order so menus cannot appear behind the header or bottom navigation.

In the native app, Starti provides safe-area inset values and the shared shell applies them to the header, login screen, content, and mobile navigation. The native top and bottom safe areas follow the selected presentation theme: light uses a light background with dark system text and icons, while dark uses dark blue-grey with light system text and icons. This updates immediately when the participant changes theme.

The notification center's “Aktivér pushnotifikationer” control is hidden by default and appears only after the Starti bridge confirms that the page runs in the native app. It is not shown in a browser.

When the Starti bridge reports that the page is running in the native app, authenticated participant pages show a small, non-fixed two-line orange “Powered by starti.app” pill after the page content. It remains hidden in a normal browser, links to Starti.app, and stays outside the primary navigation and fixed mobile navigation.
