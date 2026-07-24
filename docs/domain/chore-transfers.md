# Chore transfers

Transfer states are Pending, Accepted, Declined, Cancelled, and Expired. An assigned participant selects a suitable recipient; the server validates and creates the request; the recipient accepts or declines. Acceptance revalidates all constraints inside one transaction, changes the assignment, stores audit history, and queues only relevant notifications.

Acceptance fails cleanly if the assignment changed, recipient availability/eligibility changed, another transfer won, plan was republished, chore was deleted/archived, or child pairing would become invalid. Whole-event notifications are never sent for a transfer.
