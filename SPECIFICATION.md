# AgentBetta Specification v0.1

## 1. Executable configuration

For task `q`, AgentBetta represents the executable configuration as:

`X = <M, C, T, P, Mem, R, Tau, I>`

- `M`: model/capability tier
- `C`: context allocation
- `T`: exposed tools
- `P`: permissions/authority
- `Mem`: memory policy/allocation
- `R`: token/compute/resource budget
- `Tau`: time/turn/retry bounds
- `I`: interaction controls

Every runtime adaptation must be represented as an `AdaptationEvent` with before/after configurations, changed dimensions, reason, evidence and verification state.

## 2. Core invariants

1. **No silent permission escalation.** Adaptive logic may never grant a permission that the user/runtime did not make eligible.
2. **Selective expansion.** A diagnosis targeting one dimension may not silently expand unrelated dimensions.
3. **Observable adaptation.** Every configuration change is recorded.
4. **Verified success.** A run may be marked verified only by a validator result controlled by the runtime, not by untrusted model/tool text.
5. **Failure retention.** Failed attempts and failed contraction probes are retained in research records.
6. **Local boundary.** Local-only mode must not invoke a cloud provider.
7. **Controlled contraction.** Contraction experiments are allowed only for reproducible/non-destructive benchmark tasks unless separately approved.

## 3. Initial policy

The v0.1 implementation uses auditable heuristics. Task features include file/document need, code need, calculation need, network need, write intent, reasoning complexity cues, and requested output type.

The initial policy starts conservatively: small context, low model tier, minimal tool set, read-only permission where possible, bounded turns/tokens/time.

## 4. Verification

Validators return one of:

- `PASS`
- `FAIL`
- `INSUFFICIENT_EVIDENCE`
- `ERROR`

The default validator checks non-empty output and explicit runtime/tool failures. Task-specific validators can be supplied later.

## 5. Insufficiency diagnosis

The v0.1 diagnoser maps structured execution evidence to one or more dimensions:

- model
- context
- tools
- permissions
- memory
- resources
- limits
- interaction
- unknown

The first implementation is rule-based. Later learned classifiers must remain observable and ablatable.

## 6. Selective expansion

Expansion is monotonic within a run for the diagnosed dimension, subject to hard caps. Permissions are special: the adaptive engine may only request/activate permissions from the externally approved eligible set.

## 7. Counterfactual contraction

After verified success in research mode, the engine may propose leaner configurations by reducing one dimension at a time. The runtime records candidates; a benchmark runner may rerun safe tasks under these candidates. Real-world destructive operations must not be automatically repeated.

## 8. Learning/frontier store

The v0.1 store persists task features, configuration, adaptations, outcome and basic resource metadata as JSONL. Future policies may use these records for case-based initialization or learned prediction.

## 9. Baselines/ablations

Required modes:

- `adaptive` — full AgentBetta loop
- `fixed` — no adaptation
- `wholesale` — whole-profile escalation baseline

Switches should later permit disabling initialization, diagnosis, selective expansion, contraction and learning separately.
