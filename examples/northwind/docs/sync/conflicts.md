# Conflicts

A conflict happens when two people change the same record while offline.

## How a conflict is detected

Each record carries a version number. When a device sends a change and the version on the server is newer, the server marks the record as conflicted instead of overwriting it.

## Resolving a conflict

Conflicted records are listed in the web app under Project, then Conflicts. For each one you see both versions side by side and choose a winner per field. The losing values are kept in the record history.

## Avoiding conflicts

Assign areas or record ranges to people, and sync at the end of each day.
