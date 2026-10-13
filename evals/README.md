# evals

The factory's own evals (design: `docs/research/evals-selection.md`).

[Factory versus Superpowers](BENCHMARK.md) measures product quality, completion time,
token usage and repair work on matched changes, with isolated skills and hidden tests.
Choose execution with a shared approved spec or discovery with an independent fixed
operator policy/persona (or real human answers). Legacy recommended-answer simulation
is diagnostic only. Full Git/dirty workspaces, actual checkpoint identities, progress,
operator decisions and observed Context usage are retained. Interrupted trials can
resume, while raw and separate committed-checkpoint grades remain distinct. Human
follow-up time/rounds are manually recordable and remain null until measured.

- `cases/`: stage cases with fixtures, oracles and grading tests.
- `checkers/`: LAY-01. It needs no model. It checks that every layout checker pinned in `kit/layouts/tools.yaml` enforces a layer rule. Each checker gets a clean fixture, which must exit 0, and a planted import across the forbidden boundary, which must exit non-zero and name the file. What the runs found is in `checkers/FINDINGS.md`.

Run LAY-01:

```sh
evals/checkers/run.sh
```

It needs network access, plus `node`/`npm`, `uv` or `python3`, `go` and `cargo`. A stack whose toolchain is missing is skipped. Each tool is installed at its pin into a temp directory, and logs go there too. It prints one line per checker and exits non-zero if any expectation fails.

Benchmark grading requires macOS native sandbox support and fails closed without it. Python completion receipts reject early exits and stdout score spoofing; same-interpreter deliberate test tampering remains a documented review requirement. See [BENCHMARK.md](BENCHMARK.md) for the exact isolation and evidence limits.
