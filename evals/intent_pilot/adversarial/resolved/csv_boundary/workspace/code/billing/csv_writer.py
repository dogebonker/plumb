def render_invoice_csv(invoices):
    rows = ["invoice_id,total_cents"]
    for invoice in invoices:
        rows.append(f"{invoice.id},{invoice.total_cents}")
    return "\n".join(rows)
