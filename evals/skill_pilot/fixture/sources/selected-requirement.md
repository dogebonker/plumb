# Selected requirement export

Source: current user-requested change, supplied to this controlled local project.
Version: version unknown. Capture date: 2026-11-04.
Applicability: `ingester.accept(items, store)` requests in this project.

> Requests over five items must be rejected before storing anything; preserve accepted behavior for zero through five.

This is the requested new behavior, not a competing description of existing code.
