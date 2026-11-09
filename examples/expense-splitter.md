# Expense splitter

A small web app that splits shared expenses among a group. This brief is the demo target.

- **Goal**: help a group of friends see who owes whom.
- **Users**: group organiser, group member.
- **In scope**: create a group; add members; add expenses with an equal or percentage split; show balances; suggest the fewest settle-up transfers.
- **Out of scope**: real payments, authentication, multiple currencies.
- **Constraints**: Python 3.12, FastAPI, SQLite, one HTML page, no external services.

## Acceptance criteria

1. Given an organiser with no groups, when they create a group named "Trip", then the group exists with the organiser as its only member.
2. Given a group with two members, when a member is added by name, then the group lists three members.
3. Given a group of three members, when Ana pays 30 split equally, then Bo and Cy each owe Ana 10.
4. Given a group of two members, when Ana pays 100 split 70/30, then Bo owes Ana 30.
5. Given recorded expenses in a group, when a member opens the balances view, then every member's net balance is shown and the balances sum to zero.
6. Given balances where Bo owes Ana 10 and Cy owes Bo 10, when settle-up is requested, then one transfer of 10 from Cy to Ana is suggested.
