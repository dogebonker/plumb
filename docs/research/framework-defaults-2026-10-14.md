# Why Flask, Python and React appeared

Factory r2's choice was Flask 3.0.3, SQLite and semantic HTML/CSS/vanilla JavaScript. Its recorded rationale was maintained routing, request and cookie conventions, same-origin UI/API, and fewer unused facilities than Django. It rejected React/Express build machinery for this scope. Superpowers chose Python standard-library HTTP plus SQLite and vanilla JavaScript, explicitly rejecting Flask's package overhead. Neither chose React.

There is no explicit Flask/Python/React application-framework default in Factory's selection rules. Triage detects existing manifests or records `unknown`; it selects the React pack only when React/Next dependencies already exist. Profiles select design lenses/domain modeling, not a programming language.

Two sources of bias remain:

- The benchmark starts with `server.py` and a `benchmark.sh` that invokes Python. The brief permits replacement, but this is an implementation cue rather than a blank stack-selection experiment.
- Dedicated language guidance currently covers React/Next, Python, Rust and Go. Other frontend stacks can be identified but do not receive equivalent specialized pack coverage; many layout examples also use React/Vite/Next. More guidance is not a mandatory choice, but it can influence an agent.

FDA is an architecture/layout default, not a React or Python default. New frontend roots now prefer Fractal Domain Architecture's colocated domains and explicit browser/server boundaries. Existing layouts prevail; tiny sites/libraries and explicit team preferences may choose an alternative with a recorded reason. Factory's lightweight adaptation creates only responsibilities that exist. It does not copy inconsistent upstream agent-skill examples or invent server files for browser-only apps.

References: `skills/factory-triage/SKILL.md`, `skills/factory-architecture/SKILL.md`, `kit/layouts/index.yaml`, `kit/layouts/fda.md`, and the exported Factory/Superpowers decision records in `/Users/dan/Work/benchmark-results/codex-fullstack-20261013-r2/`.
