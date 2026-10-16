Demo call, Northwind Field Logger, 45 minutes. Attendees: Lena Vogt (prospect, operations lead), Marcus Oyelaran (prospect, GIS specialist), Sales.

Sales: Thanks for joining. You said the main pain is the weekly hand-over of data to your office team. Let me start there.

Lena Vogt: Yes. Every Friday someone exports the week's records to CSV and emails them. It is manual and it gets forgotten.

Sales: You can schedule that. In the project, under Exports, there is a Scheduled exports tab. You pick the forms, the format, the interval, daily or weekly, and the recipients. The export runs on the server and the recipients get an email with a link. You can also point it at an SFTP folder instead of email if your IT prefers that.

Marcus Oyelaran: Does the scheduled export use the same filters as the manual one?

Sales: Same filters, yes: form, date range, member. The date range is relative for a schedule, so "last 7 days" rather than fixed dates.

Marcus Oyelaran: Good. Second question, GeoJSON. Our GIS team works in a projected system, not WGS 84. Can the export be in our system?

Sales: The GeoJSON export is always WGS 84, which is what the GeoJSON spec asks for. The CSV export has latitude and longitude in WGS 84 too. Reprojection happens in your GIS. The project setting for the coordinate reference system only affects how positions are displayed in the app.

Lena Vogt: What about validation? Our forms have a lot of rules and the collectors get frustrated when they cannot save.

Sales: Rules run on the device and work offline. Each rule has a message, and we recommend keeping it short and saying what to do. Range, pattern, required-if and cross-field rules are all there.

Lena Vogt: And conflicts, two people editing the same record?

Sales: Each record has a version number. If the server has a newer version than the one a device sends, the record is marked as conflicted and nobody's data is lost. An editor resolves it in the web app field by field.

Marcus Oyelaran: Last one. We have about 40 forms built in another tool. Can we import them?

Sales: There is a form import from a JSON or XLSForm file. Under Forms, choose Import, and pick the file. Field types map automatically where possible and you get a report of anything that needs attention before the form is saved. If you send me a sample at sales@northwind.example I can run it with you. You can also reach me on +1 (415) 555-0142.

Lena Vogt: Perfect. I will send one over, lena.vogt@example-infra.com is my address for the follow-up.

Sales: Great. I will send the summary by Monday.
