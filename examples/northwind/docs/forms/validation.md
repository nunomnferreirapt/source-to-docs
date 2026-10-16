# Validation rules

Rules check a record before it can be saved.

## Rule types

- Range: a number must be between a minimum and a maximum.
- Pattern: a text value must match a regular expression.
- Required if: a field becomes required when another field has a given value.
- Cross-field: compare two fields, for example end time after start time.

## Messages

Each rule has a message shown to the user when it fails. Keep messages short and say what to do, not only what is wrong.

## Rules and offline work

Rules run on the device, so they work without a connection. Changing a rule in the web app reaches devices on the next sync.
