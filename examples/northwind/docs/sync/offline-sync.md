# Offline sync

The app stores records on the device and sends them to the project when a connection is available.

## How sync runs

Sync starts when the app opens, when a record is saved and a connection exists, and every 15 minutes while the app is in the foreground. You can also pull down on the record list to sync now.

## What syncs

Records, photos and form versions. Photos sync after records, so a record can appear on the web before its photos do.

## Sync status

Each record shows one of: pending, sent, or failed. A failed record keeps its data and is retried on the next sync. Open the record to see the error.

## Storage

The app keeps records on the device until they are sent and confirmed. Photos are kept for 30 days after sending, then removed from the device.
