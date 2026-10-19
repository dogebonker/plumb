The 19 fixed check groups exercise the supplied FR/NFR contract through HTTP and
accessible UI behavior. All framework/layout choices are free within those boundaries.
Each group carries requirement IDs; the runtime aggregates them into the five fixed
user outcomes in case.json. These are coverage/evidence results, not proof of every
possible implementation property or a production security certification.

The trusted runtime captures the final data through HTTP in its own memory, restarts
the owned server group, and compares the result. A read-only database test restarts
before testing writes so previously opened file descriptors cannot invalidate the
failure injection. Startup refusal is safe; after permissions are restored all prior
records must remain, and retry must succeed exactly once. Corruption is deliberately
applied only to the disposable DATABASE_PATH, never the submitted app's original data.

Automated UI checks cover combined filters, create/edit/comment, HTTP save failures,
stale edit conflicts, native keyboard operation and modal containment, overflow/title
readability and screenshots at 360/600/601/1280. Visual maturity, brand fit, comprehensive
accessibility and additional security findings need the separate blinded review.

Application reset/start has a separate macOS native policy: clean environment,
local-only network, copied product and its own runtime directory. Submitted code
cannot read hidden grader files/runtime or read/write grading artifacts. The trusted
observer relays server stdout/stderr into its log; artifact handles are not inherited. Dependencies are copied
from project-local node_modules/.venv, not installed during grading. Escaping dependency
links are rejected except canonical Python interpreter links verified by probes of
fixed installed system locations and the observer interpreter. Only those verified
public runtime prefixes become readable; submitted links are never executed as probes. Console shebangs, shell trampolines and activation paths relocate into the
copied venv. Raw server logs and screenshots are retained. Every launched process group is
owned and killed on completion, startup failure or timeout; unrelated groups are left
alone. Individual readiness/grading deadlines protect a hung check, not the model's
implementation budget.
