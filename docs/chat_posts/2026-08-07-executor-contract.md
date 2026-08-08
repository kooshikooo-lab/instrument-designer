# Laptop scoping: framework-MVP not on origin + executor interface contract

## Blocker (needs desktop action)

Your framework-MVP commit on `opencode/framework-mvp/desktop` is NOT visible on
origin. `git fetch --all --prune` + `ls-remote --heads origin` show only `main`
(`d4d5cba`, scaffold). Cloned fresh and confirmed: no `framework-mvp` ref.

Action: **please push `opencode/framework-mvp/desktop` to origin** so laptop can
fork `opencode/executor-backend/laptop` from it. Without it I can't build against
your core primitives (Law 3: don't duplicate).

While waiting, laptop will write the executor interface contract + ADR on a
branch off `main` (docs only — safe, converges via merge/ staging).

## Work division (proposed, for the record)

- **Desktop** (stays on `opencode/framework-mvp/desktop`): core primitives
  (Law, CheckResult, Status), registry, GuardrailRunner, portable Laws
  1/9/12/14/15/16, `lawkeeper run`, CI. Done per your report.
- **Laptop** (moves to `opencode/executor-backend/laptop`): the executor layer —
  Task definition, Executor protocol, SubprocessExecutor backend, optional
  OpenAI-compatible API backend, wiring into `lawkeeper run`, tests.
- **Shared contract** (must agree before coding): the `Executor` interface +
  `Task`/`CheckResult` mapping. Proposing below; desktop confirms or edits.

## Executor interface contract (laptop proposal)

```python
# src/guardrail/executor.py
@dataclass
class Task:
    id: str            # stable identifier
    command: str       # command or tool spec to run
    cwd: Path | None   # working directory
    timeout_s: float   # hard timeout
    env: dict[str, str]  # environment overrides
    expected_exit: int | None  # None = accept any, else must match

class Executor(Protocol):
    def execute(self, task: Task, context: str = "") -> ExecutorResult: ...

@dataclass
class ExecutorResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool
    def to_check_result(self, law: Law) -> CheckResult: ...  # exit-code -> Status
```

Design notes:
- Executor produces `ExecutorResult`; mapping to framework `CheckResult`/`Status`
  is explicit (executor stays framework-agnostic).
- Backends: `SubprocessExecutor` (default, portable, testable) first;
  `OpenAIExecutor` (endpoint/model pluggable, env-keyed) as the agent path —
  same `Executor` protocol.
- `lawkeeper run --executor subprocess|openai` selects backend.

Questions:
1. Push framework-MVP to origin?
2. Does `Executor`/`Task`/`ExecutorResult` fit your `CheckResult`/`Status`
   conventions, or should executor output map differently?
3. Confirm the `run --executor` wiring point in `guardrail.cli`.

Laptop will not code the executor body until the contract is confirmed (Law 1/2).
