# Batch limit design

Observed: `ingester.accept` iterates items, appends each to store, returns count.
Only caller: `test_ingester.py`; inspected all project Python and knowledge files.
No exports, config, fixtures, services, imports or persistent storage need changes.

Proposed: materialize the finite request once, reject length >5 with ValueError,
then use the existing append loop. Materialization preserves iterator input and
lets rejection occur before any storage call. Store interface and success return
value stay unchanged. No dependencies or migrations. Rollback is a local code revert.

Unknown: external callers and real storage adapters are unavailable; local checks
prove only the inspected fixture. Infinite iterables are outside this finite-request
fixture; full materialization has input-size-dependent memory, which would require
bounded consumption if this ingress handled unbounded streams. Store failures keep
the existing partial-write behavior; transactions are outside the size-limit request.
