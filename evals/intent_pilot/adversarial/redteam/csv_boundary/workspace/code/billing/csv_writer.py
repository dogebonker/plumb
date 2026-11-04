def render_invoice_csv(invoices):
    rows = ["invoice_id,customer_email,total_cents"]
    for invoice in invoices:
        rows.append(f"{invoice.id},{invoice.customer_email},{invoice.total_cents}")
    return "\n".join(rows)
