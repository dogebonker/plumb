# Constraints: support-ticket-dashboard

Standing requirements, promises and constraints of this project. Every change reads this file. Each row ends mapped to an enforcement.

| ID | Kind | Statement | Fit criterion | Source | Enforced by |
| --- | --- | --- | --- | --- | --- |
| SYS-NFR-01 | validation | Bad input is rejected at the door | required fields are trimmed and validated before any ticket is stored; invalid input creates nothing | nfr-catalog/web-api | unmapped (test) |
