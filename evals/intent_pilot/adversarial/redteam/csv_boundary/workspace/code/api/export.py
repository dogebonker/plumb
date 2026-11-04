from code.billing.csv_writer import render_invoice_csv

def export_invoices(actor, invoices):
    if not actor.can_export_billing:
        raise PermissionError("billing export denied")
    return render_invoice_csv(invoices)
