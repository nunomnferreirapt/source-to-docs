# Export to CSV and GeoJSON

Exports are made in the web app under Project, then Exports.

## CSV

One CSV file per form. Columns are the short names of the fields, plus record id, created at, created by, form version and position (latitude and longitude).

## GeoJSON

All records with a position, as a FeatureCollection. Field values become properties. Records without a position are skipped.

## Filters

Filter by form, date range and member before exporting. The filter is written into the export file name.

## Photos in exports

CSV and GeoJSON exports contain the photo file names, not the photos. Photos can be downloaded one by one from a record.
