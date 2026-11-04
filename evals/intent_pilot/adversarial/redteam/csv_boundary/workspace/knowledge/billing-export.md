# OKF: Billing export
Current invariant: only actors with can_export_billing may export invoices; the API entry point enforces it.
CSV currently includes customer_email.
Source: sources/notion-export.md.
Historical note (2025): the serializer must enforce the export permission itself.
Future idea: stream rows directly from the database; no accepted decision exists.
