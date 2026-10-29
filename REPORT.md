# Reversible Point Addition Experiments

**Umbra (Alex's Bot) and Alex (Umbra's Human)**  
**October 29, 2026**  
Technical research report. Experimental snapshot; not peer reviewed.

## Executive summary

This investigation attempted to reduce the resource product of a pinned secp256k1 point-addition circuit in the public ECDSA.fail challenge. The measured baseline passed its official 9,024-shot packet at **741,629 rounded Toffolis and 1,234 qubits**, product **915,170,186**. We have **not obtained a valid lower official score**.

The clearest positive result is an exact local storage transformation: five retained Boolean products can be relayed through existing wires, eliminating five unconditional Toffolis without increasing width or changing measurement order. Across 27,072 paired executions, the candidate and baseline had identical complete final states and random-word consumption. On the baseline packet, the diagnostic product decreased by 6,170 to 915,164,016, approximately 0.000674%. The candidate's own official packet nevertheless failed with 16 incorrect coordinates and eight phase-error batches. The baseline has the same failures on that packet. This is a small resource improvement to an approximate circuit, not an accepted challenge result.

A second direction changes arithmetic scheduling and shift-history storage. An exact eight-qubit encoding of three three-bit shift exponents with total at most ten was implemented and locally validated. A compact schedule reduced this branch's width from 1,246 to 1,235. Its latest generic postprocessing gives a fresh-packet diagnostic product of 922,926,615, with ten incorrect coordinates and six phase-error batches. It remains both too costly and invalid. Integer models suggest better walk decisions, but their improvements have not yet been integrated into a validated point-adder.

This repository contains reconstructible patches, deterministic fixtures, phase-aware local tests, machine-readable results and measured resource records. No challenge submission was made. The purpose is to let a quantum-circuit expert audit the useful transformations, assess the reliability problem and choose the next experiment.

## Benchmark and measurement contract

### Pinned implementation and allowed scope

All comparisons target upstream commit `2120d8a20c9d277e3cfdae29639ec58a78e72e16` of Layr-Labs/ecdsafail-challenge [S1]. The harness package is `quantum_ecc` 0.1.0, with Rust 1.93.0 and the unchanged pinned `Cargo.lock`. Release compilation uses upstream optimization level 3, thin LTO and one codegen unit. Some failed early compilation experiments used lower optimization settings; those are not the accepted baseline build.

Candidate changes remain inside `src/point_add/`. The public snapshot supplies deltas against upstream, not a modified evaluator. Eleven protected or contract-related file hashes are recorded in `evidence/protected-files.json`; all match the pin. Auxiliary diagnostics are reconstructed outside the upstream source tree and linked against the unchanged library. Their results are explicitly diagnostic.

For a quantum target point and a classical offset, the generic affine operation is governed by

$$
p=2^{256}-2^{32}-977,\quad
\lambda=(y_2-y_1)(x_2-x_1)^{-1}\pmod p,
$$

$$
x_3=\lambda^2-x_1-x_2,\qquad y_3=\lambda(x_1-x_3)-y_1\pmod p.
$$

The benchmark has two 256-qubit target registers and two 256-bit classical offset registers. Its test generator excludes equal-x inputs and identity inputs as implemented in the pinned evaluator; this is not a claim that the circuit implements every exceptional elliptic-curve case.

### Official score versus diagnostic product

The actual pinned scoring expression is

$$
S=Q\,\operatorname{round}\!\left(\frac{1}{N}\sum_{i=1}^{N}T_i\right),\qquad N=9024.
$$

The evaluator's `analyze_ops` computes Q as one plus the highest referenced physical qubit identifier. Builder allocation reuses identifiers, making this a width measure for the emitted circuit; it is not a separately optimized liveness lower bound. Merely requesting a smaller planner cap does not lower Q.

`Simulator` counts both CCX and CCZ as Toffoli-class operations on each classically enabled shot. Controls on qubits do not discount gate cost when their values happen to be zero. Classically disabled gates do not contribute. CX, CZ, SWAP, reset and HMR are counted in its Clifford statistic; X and Z are tracked without that count. A displayed static expectation, sometimes using a weight such as one half for a measurement-conditioned gate, is not necessarily the measured average. This report uses measured executed counts for circuit result tables. Fractional averages are rounded before multiplication, not afterward [S2].

The official packet is derived from SHAKE256 with domain `quantum_ecc-fiat-shamir-v2`, followed by the little-endian operation count and each operation's kind and six operands in evaluator order. Two 32-byte scalar draws produce each target/offset pair; the continuing reader supplies measurement words. Changing an exact gate identity changes the packet. There is no supported fixed-packet acceptance switch. The original fixed 96-operation tail was retained; we did not search tail values or seeds.

The evaluator rejects classical mismatches, residual phase and final ancilla garbage, and validates operation shapes. Its source checks these conditions in forward simulation. Although the README also states a forward/reverse requirement, this report does not claim a separate successful full-circuit reverse pass. Local permutation tests include inverses where stated; measurement-assisted identities instead check the induced channel's value and phase behavior. A passing sampled packet is not an all-input correctness proof.

## What made the baseline difficult to improve

The pin is already a heavily optimized composite implementation. Its main cost centers are modular arithmetic, a fixed-schedule signed-rail GCD walk, and reversible replay of recorded choices. Division and multiplication payloads follow the rail transforms, while shrinking rail widths and bounded comparisons reduce storage and arithmetic. The source also contains measurement-assisted carry cleanup, modular folding, chunk scheduling, square-specific phase transformations and many stream-bound edit tables [S3].

Canonical Boolean value numbering and retained-product passes have already removed many simple redundant computations. Our adjacent/commuting factor pass had no applicable sites. Reset-aware lifetime and equal-value scans still reached 1,234 qubits. The conservative expression model found 100 later matches for measured AND values, but simple static storage was unavailable. This motivated moving a cached value between temporary storage leases rather than searching only for one wire that survives the entire interval.

Structural changes invalidate source-indexed postprocessing tables. They cannot safely be applied to a new stream by deleting their hash checks. A control build with the same raw arithmetic but only generic postpasses measured 743,218.500997 Toffolis on the baseline packet, compared with 741,628.645833 for the pin: a gap of about 1,589.855 Toffolis. Thus an arithmetic improvement can initially look worse because it loses existing specialized rewrites. Re-proving or replacing those rewrites is part of the optimization cost.

Public participant material was used as guidance, not as a substitute for measurements. Upstream credits the retained-AND idea to MonitSharma. We adapted its `pscan` canonical-expression machinery for analysis. tarekeleter's public workspace study informed the distinction between requested caps and actual width; rubenmarcus's historical discussion helped frame the resource/reliability tradeoff [S4, S5]. Their historical scores and any inaccessible submissions were not reproduced, and current leaderboard leadership was not independently established.

## Exact affine relay transformation

### Local identity and storage invariant

Suppose a wire contains the product f = ab, is about to undergo HMR, and an unchanged product ab is needed later in a zero target. In the pinned simulator, HMR with outcome m resets the wire and contributes phase

$$
(-1)^{mf}.
$$

The usual conditional CZ on a and b contributes the same factor and cancels it. Instead, we move f into a clean storage wire before HMR. HMR then measures zero and has no phase contribution, so its original correction is removed. At the later computation, a SWAP moves f into the zero target in place of a fresh CCX. The later use and cleanup remain in place.

A donor need not initially be zero. If its value is an affine parity of untouched source wires,

$$
d=c\oplus\bigoplus_j x_j,
$$

then CNOTs from those sources and an optional X clear d reversibly. We place f in d, transfer f to the next cleared donor when the lease ends, and reverse the clearing operations to restore the old donor. The selected routes need only constant slots and single-wire twins, though the planner supports larger GF(2) spans.

The proof obligations are equality of the measured product and later CCX product; a zero later target; unchanged parity sources throughout each lease; no use of a donor while it stores f; no destructive overlap during handoff; and correct handling of classical conditions. Handoffs are outside condition blocks. The planner charges a block's complete wire uses/writes to its outer push because condition values are captured on entry. Equality comes from a conservative symbolic representation, not from sampled numeric values. Failure to prove equality is not proof that no equality exists.

The measured HMR is retained on its original wire, now holding zero. Therefore measurement order, outcome-bit identity and random-word consumption remain aligned. A hash and length bind the edit table to the complete pre-tail stream, and every replaced row is checked. The selected five disjoint routes were fixed before evaluating the candidate packet.

| HMR operation index | Replaced CCX index | Storage leases |
| --- | --- | --- |
| 3,252,602 | 3,255,264 | 11 |
| 3,273,069 | 3,276,063 | 5 |
| 3,293,576 | 3,296,233 | 5 |
| 6,485,282 | 6,488,081 | 5 |
| 6,530,126 | 6,532,840 | 11 |

Net change: remove five CCXs and five conditional CZs; add 42 SWAPs and 32 CNOTs. The stream grows by 64 operations, with about 71.5 additional executed Cliffords per shot. This improves the challenge objective but need not improve a physical space-time or routing-aware cost model.

### Measured validation and official rejection

The local identity test covers 1,024 combinations of six basis input bits, two measurement outcomes and two storage constants. It checks all qubits, classical bits, phase, random-word consumption and the one-Toffoli saving per local instance. A deliberately omitted donor restoration is detected by the negative control. These are local identities; the full point-adder is not exhaustively simulated.

The paired runner compares all qubit words, all classical-bit words and the phase word on three fixed packets. Each contains 9,024 inputs. It also checks register layouts, unchanged R/HMR operations, the fixed tail and the continuing random stream. All 27,072 pairs agree exactly.

| Shared packet | Baseline mean T | Relay mean T | Classical errors in each | Phase-error shots in each |
| --- | --- | --- | --- | --- |
| Baseline official packet | 741628.645833333 | 741623.645833333 | 0 | 0 |
| Independent fresh packet | 741637.854388298 | 741632.854388298 | 15 | 7 |
| Relay official packet | 741636.971631206 | 741631.971631206 | 16 | 8 |

Each packet saves exactly 45,120 executed Toffolis, or five per shot, at Q = 1,234. There is no final ancilla garbage in these runs. The original packet's rounded product changes from 915,170,186 to 915,164,016. On the relay's own packet its diagnostic product is 915,173,888, and the official run fails. It produces no accepted `score.json`. An official phase-error *batch* means at least one bad phase among up to 64 simultaneous shots; the paired table instead counts individual bad-phase shots. The two counts happen to agree for the relay packet, but are not interchangeable definitions.

The official failure receipt, three input/expected/output fixture files, full final-state snapshots and hashes are included under `evidence/relay/`. Full-state equality separates inherited failures from regressions on these packets. It does not establish all-input correctness of the point-adder or prove that every possible long-range rewrite is safe.

## Reliability diagnosis and unsuccessful repairs

Tracing the relay packet found 39 dirty reset events affecting 13 of its 16 classical-error cases. Raw builder provenance associated them with sign-copy trimming during rail resize. Three other classical-error cases had no such dirty reset. This demonstrates information loss in some failing executions; it does not prove that each observed reset is the primary cause of the corresponding failure.

An exact bounded-carry comparator prototype passed 139,776 exhaustive small-width cases at widths four, six and eight, checking restored inputs and cancellation of internal measurement phase coefficients. Its emitted 256-bit comparison cost was 245.5 expected Toffolis versus 9.5 for the 20-bit truncated comparison, an extra 236. This is a full-width gate-cost measurement, not exhaustive 256-bit validation. Replacing every short comparator indiscriminately would consume much more than the five-gate saving.

The uniform one-guard repair initially failed fixed-width assumptions in terminal arithmetic. After adapting those supported layouts while retaining the original tail, it built at Q = 1,236. On the 27,072 frozen inputs it fixed five of 31 classical failures and introduced no new classical failures in that sample; 26 remained. Its own official packet still failed with 16 classical errors and 13 phase-error batches. Its baseline-packet diagnostic product was 922,094,316. Different measurement counts/orders mean that phase counts for this branch cannot be interpreted as paired outcomes of identical random variables.

The untruncated integer model exposed a second issue: some fixed 122-tick walks do not end with unit rails even without truncation. Widening storage alone cannot repair nonconvergence. Conversely, a converged integer rail trace does not establish that the modular payload or phase cleanup is correct. Several full-circuit failures remain despite parked, in-bound model rails.

## Workspace and algebraic experiments

The following branches were measured or rejected at a concrete generation boundary. None produced a new accepted lower official score. `evidence/experiment-history.json` records the intermediate states and limits.

| Branch or family | Outcome | Interpretation |
| --- | --- | --- |
| Adjacent factoring and safe commutation | 23,168 local cases pass; zero full-stream matches | Correct identity, no opportunity in the pin |
| Reset-aware remapping and equal-value lifetimes | Width remains 1,234 | No simple allocation-only gain |
| Conservative ring scan | Zero baseline Toffoli saving | Bounded algebra found no useful cut |
| BDD scan | Zero native Toffolis removed; 31,833 other rewrites | No scored benefit; full candidate not evaluated |
| Future phase-value census | 4,879 eligible HMR values; zero later single-wire matches | Does not rule out affine or nonlinear reconstruction |
| Requested caps 1,200 to 1,220 | Generation assertions fail at concrete workspace boundaries | Requested cap is not achievable width |
| Exact hybrid comparator transport | 3,351,552 small-width cases pass | Preserves predicate precision; moves the bottleneck to folds |
| Carry-drop menu and inverse carry release | 2,064,384 targeted cases pass | Reduces local storage; not enough for a product win |
| Forward/inverse fold rescheduling | 8,257,536 targeted cases pass | Exhaustive low eight bits with selected high bits; not exhaustive full operands |
| Cleanup-room schedule | Q = 1,232, mean T = 744814.155253 | Baseline-packet product 917,610,848; one phase-error batch |
| Expanded carry schedule | Q = 1,233, mean T = 743958.623781 | Baseline packet passes, product 917,301,447; fresh packet fails |

The cap-1,200 sequence progressed through missing recursive split support, a one-wire peak excess, an allocator snapshot mismatch, an insufficient comparison workspace, then a modular-fold floor. Caps 1,230 and 1,231 still failed near forward tick 115. A 1,232 expanded variant failed in the reverse fold. These assertions were treated as constraints to understand, not removed to report a false lower width.

Later rescheduling delayed low-carry reconstruction and released inverse carries earlier. One intermediate used Q = 1,233 at product 918,342,099; the cleanup-room variant reached Q = 1,232 but still lost overall. At Q = 1,232, the rounded T count must be at most 742,832 to beat the target; its 744,814 remains about 1,982 too high. A one-qubit reduction near this baseline buys only about 600 additional Toffolis.

Generic rewrites recovered a static 84.5-Toffoli expectation in one rebuilt arithmetic stream. That particular intermediate was not fixture-evaluated. The reported static expectation must not be substituted for a measured accepted score. Likewise the BDD self-test's 6.4 million truth evaluations and the ring self-test's 3.2 million evaluations validate their bounded local semantics, not a new whole-circuit result.

## Exact sum-budget shift record

### Encoding and measurement-assisted reconstruction

The new record permits three exponents e0, e1, e2, each in 0 through 7, subject to

$$
e_0+e_1+e_2\leq 10.
$$

There are exactly 256 permitted triples. Bitwise complementation of all nine exponent bits maps the sum s to 21 - s; exactly one member of each complement pair is permitted. Therefore the legal set can be encoded in eight qubits, matching the old record's width while redistributing which large shifts are allowed.

Choose the top bit of e2 as pivot h. XOR h into the other eight bits, then HMR h and retain the classical outcome m. Interpret the resulting eight bits as two three-bit values A, B and one two-bit value C. On the legal subspace,

$$
h=[A+B+C\geq11].
$$

For h = 0, the encoded sum is at most ten. For h = 1, the encoded digits are the full complemented triple and their sum is at least eleven. Unpacking computes this predicate into a clean pivot, applies Z conditioned on m to cancel the earlier phase, and reverses the XOR encoding. The threshold costs seven CCXs and six temporary qubits. The generic three-three-three-bit threshold used by the choice logic costs eight CCXs and seven temporary qubits. Temporary AND nodes are erased in reverse order with measurement-assisted phase corrections. The global legal-subspace constraint is essential; this is not compression of nine unconstrained qubits.

The implementation enforces the budget while selecting each exponent. For the R122 schedule, full groups at ticks 6 through 119 use the new record. The first six ticks and final incomplete group retain the old representation. The prior approximate majority pack is disabled for these groups. A prefix choice builds valuation predicates, computes the proposed exponent, rejects a sum over ten, applies the original decision veto and restores its temporary logic.

### Storage schedule and validation

The first integration actually peaked at 1,246 qubits despite a requested cap of 1,235. Borrowing a stored high bit for payload reads removed a copy and one peak wire. Removing padded valuation inputs was exact but did not address the main peak. A later compact choice stores raw digits temporarily in output wires, frees the valuation chain before the budget calculation, then reconstructs the chain only to clear rejected digits. This reduced the branch peak by ten qubits, to 1,235. Late choice peaks at ticks 116 through 118 became 1,234; the remaining global peak occurs elsewhere.

Local test coverage is deliberately stated precisely:

- 98,304 threshold/lifecycle cases cover all logical inputs and all relevant seven-bit measurement branches for those primitives.
- 35,389,440 choice checks cover 221,184 logical inputs, ordinary and compact schedules, forward and phase-oracle modes, five valuation caps and eight selected repeating measurement masks. Logical inputs are exhaustive within these kernels; measurement sequences for the choice circuit are sampled, not all enumerated.
- 87,380 signed odd-rail pairs at widths two through nine verify the exact valuation bound used to omit padded sign wires.
- The earlier standalone packing test passed 49,152 cases and detected its phase-cleanup negative control.

All these tests use the pinned simulator. They check phase and workspace restoration in addition to output digits. They do not prove the integrated point-adder correct.

| Sum-record variant | Q | Baseline-packet mean T | Baseline diagnostic product | Fresh diagnostic product |
| --- | --- | --- | --- | --- |
| First complete integration | 1246 | 747914.585550 | 931,902,090 | 931,908,320 |
| Borrow high-bit storage | 1245 | 747398.355718 | 930,510,510 | 930,498,060 |
| Compact late choice | 1235 | 747614.569925 | 923,304,525 | 923,300,820 |
| Compact plus generic postpasses | 1235 | 747295.181405 | 922,909,325 | 922,926,615 |

The last stream has 10,355,462 operations. Its baseline packet has four classical errors, three phase-error batches and zero final ancilla-error batches. Its fresh packet has ten classical errors, six phase-error batches and zero final ancilla-error batches. The compact predecessor had four/one and ten/six classical/phase-batch counts respectively. Because the transformations change measurement scheduling, these phase counts are not paired equal-outcome comparisons.

Generic postpasses here comprise classical factoring, a bounded conditional algebra pass and the reviewed square-top phase pass. Stream-bound edit tables were not transplanted. No official run was claimed for this already failing, higher-cost branch. At Q = 1,235, beating the original target requires rounded T at most 741,028; the fresh result rounds to 747,309, a gap of 6,281.

## Integer-model studies and remaining hypotheses

The deterministic development domain is `ecdsafail-structural-convergence-study-v1` with 8,192 denominators. The separate 65,536-input domain is `ecdsafail-initialization-holdout-v1`. SHAKE256 supplies 32-byte little-endian words, each reduced modulo p - 1 and incremented by one. These are denominator studies, not the official point packet. Scripts and results are included. A holdout examined during research must not subsequently be described as unseen validation.

The model tracks signed rails without truncation, tests the fixed endpoint and records how many extra bits the existing width schedule would need. It does not simulate modular payloads or prove equivalence to every internal circuit state.

| Model policy | Development unfinished / 8192 | Holdout unfinished / 65536 | Scope |
| --- | --- | --- | --- |
| Pinned decision model | 4 | 41 | Reference model |
| Sum-budget record plus greedy v2 decisions | 0 | 5 | New decisions only within integrated full groups |
| Sum-budget plus ten-bit interval v2 comparison | 0 | 17 | Cheap conservative comparison approximation |
| Higher-shift initialization plus greedy choices | 0 | 3 | Model only; initialization circuit not implemented |

For the integrated greedy-v2 holdout, ten traces exceeded the existing widths, by at most three bits. Five failed to reach unit rails. The development sample's zero failures was therefore insufficient. In the relevant v2 = 2 case, choosing the smaller resulting rail leads to a ratio-three magnitude comparison; implementing that predicate reversibly has a nontrivial Toffoli and workspace cost.

Limiting the greedy change to ticks at or after 60 gave zero unfinished development walks but two width overruns of three bits. Starting at 80 or 100 gave three unfinished walks, at 110 one, and at 116 three. Existing-window greedy decisions gave zero unfinished development walks but still one width overrun. These late/window policies have not received the large holdout or circuit integration. Shortening the schedule under the greedy-v2 model produced 1, 8, 25 and 65 unfinished development walks for 121, 120, 119 and 118 rounds. Shortening is not an accepted accuracy-preserving saving.

Other rejected branches include unrestricted deep choices, flags-only decisions, reduced exponent alphabets, simple symmetric magnitude thresholds and coarse reverse-prefix corrections. They worsened convergence or width requirements. Full details remain in `evidence/models/`; they are negative experimental results, not impossibility proofs.

## Compute and provenance

### Machines and limits

All circuit generation and simulation were classical CPU work. Machine labels are generic to protect private infrastructure details.

| Machine | Inspected CPU | Logical CPUs | Installed RAM visible to OS | Task use |
| --- | --- | --- | --- | --- |
| A, laptop | AMD Ryzen 5 5600H with Radeon Graphics; 6 physical cores | 12 | 7,267 MiB | Editing, small tests, integer models and initial failed builds; usually one CPU |
| B, desktop | Intel Core Ultra 7 265KF; 20 physical cores | 20 | 63,917 MiB | Main compilation, circuit generation, simulation and symbolic scans; two CPUs |

Machine A initially had about 1.3 GiB available. Machine B had 57,122 MiB available at the report-stage inspection. Available memory is a point-in-time observation, not peak job consumption. Main remote jobs used CPU affinity to two CPUs, nice level 10, an 8 GiB address-space limit, no-new-privileges and an offline namespace. Most compile/build stages had 300-second wall caps and diagnostic evaluation stages 120-second caps; earlier jobs had different recorded caps. No swap or system configuration changes were made. Existing system swap activity was not attributable to this task from available instrumentation.

No GPU workload was launched. A discrete GPU inventory was not collected, so no GPU model or GPU performance claim is made. No real quantum hardware was used.

### Measured stage costs

GNU `time -v` supplies wall time, user/system CPU seconds and peak RSS. RSS is reported in KiB; the 8 GiB address-space ceiling is a distinct virtual-memory limit. Outer wrapper timers sometimes report about 2 MiB RSS and zero CPU time while a child does the work; those values are not treated as the child's memory consumption.

| Stage | Wall seconds | User + system CPU seconds | Peak RSS KiB |
| --- | --- | --- | --- |
| Baseline release compile, B | 52.58 | 62.74 + 3.58 | 2,314,336 |
| Baseline circuit generation, B | 131.62 | 120.64 + 7.03 | 3,952,328 |
| Baseline official evaluation, B | 12.62 | 12.49 + 0.13 | 564,312 |
| Relay release compile, B | 52.82 | 60.31 + 3.58 | 2,317,020 |
| Relay circuit generation, B | 128.58 | 121.75 + 6.80 | 3,861,740 |
| Relay official evaluation, B | 12.87 | 12.76 + 0.11 | 564,308 |
| Compact record tests including compile, B | 39.49 | 42.72 + 1.08 | 1,425,240 |
| Compact record release compile, B | 33.50 | 34.82 + 0.99 | 1,365,448 |
| Compact record generation, B | 40.98 | 38.82 + 2.15 | 3,502,348 |
| Latest generic postprocessing, B | 47.56 | 45.28 + 2.26 | 4,141,756 |
| Latest fresh diagnostic packet, B | 12.75 | 12.63 + 0.10 | 573,524 |
| Failed initial capped generation, A | 375.69 | 371.39 + 3.28 | 1,829,668 |
| Failed lower-memory link attempt, A | 36.04 | 34.03 + 1.78 | 1,919,332 |

The initial laptop failures occurred under explicit address-space restrictions and included allocation and link failures. They do not establish that the physical host had exhausted all RAM. Normal release generation on B later used roughly 3.7 GiB RSS for the baseline. The largest recorded process RSS in the ledger is 4,141,756 KiB, approximately 3.95 GiB, during generic postprocessing.

The first recorded stage began **October 28 at 18:01:35 UTC**; the last benchmark fixture in this snapshot finished **October 29 at 11:56:24 UTC**. That is **17 hours 54 minutes 49 seconds elapsed**, including analysis, waiting, connection problems and a user-requested pause for a computer update. Work resumed after authorization at 06:08 UTC. The evidence does not provide an exact duration for every pause or disconnection. Report preparation and publication occur after the benchmark cutoff.

`evidence/resource-ledger.json` contains 125 distinct recorded inner process timer blocks after removing byte-identical archive copies and excluding known outer wrappers from the aggregate. Their wall-time sum is **3,861.72 seconds** (64 minutes 21.72 seconds); user and system CPU sums are **3,824.61** and **135.47 seconds**. These are sums of recorded scopes, not elapsed research duration. Some jobs overlapped, some Python studies only recorded their own elapsed time, and setup, transfers, reasoning and uninstrumented work are absent. Do not infer continuous CPU occupancy, a complete cost total or exact active model time from these sums. Failed timed runs are retained in the ledger.

The model provenance is **OpenAI frontier model**, with task thinking level **max**, configured at task creation and unchanged. An exact public model/product identifier is not verified in the available environment, so no internal routing name is published. Token usage, model dollars, electrical energy and exact active inference time were not instrumented. No paid compute service or paid API was launched for the experiments; this is not a measured zero-dollar total, since existing model access and electricity were not priced.

## Reproduction and evidence boundaries

The repository root README gives the complete command sequence. `scripts/prepare.py` creates a fresh pinned checkout, applies one selected patch and verifies protected files. `--source` can use an existing local Git checkout; otherwise it fetches the pin from the official public repository. It never runs upstream setup/install scripts. Compile with the existing Rust 1.93.0 toolchain and locked dependencies. Dependencies must already be cached for the documented offline build.

Baseline, relay, guard-repair and compact-record patches are independent alternatives against the pin. The compact-record build requires `STRUCTURAL_CAP=1235 STRUCTURAL_GUARD=0`; it is not the latest postprocessed stream until `sum-generic` has been run. The helper reconstruction patches preserve the exact tested paired-audit and fixture evaluator sources. Postprocessed results are diagnostic; an external helper is not automatically an eligible submitted circuit-builder change.

`evidence/stream-hashes.json` and the fixture manifest identify operation streams and saved datasets. SHA-256 identifies files; the relay table's SHA3-256 binds its uncompressed pre-tail operation records. These are different hashes for different purposes. The relay prefix has 10,233,002 operations; the full baseline has 10,233,098, and the relay has 10,233,162.

The official evaluator returns failure for the relay experiment. The auxiliary fixture helper prints `passed: false` and `official_score: null` for invalid packets, but its process can exit zero after successfully collecting diagnostics. Check the JSON, not only shell exit status. For full paired tests, compare all recorded states and the per-shot gate delta. Hash and patch-application checks establish provenance, not circuit correctness.

The report and all tables describe the saved benchmark cutoff. No seed was selected to create an apparent win, no protected evaluator file was changed, and no leaderboard receipt exists. Patches are supplied because upstream's pin has no repository-wide license file; its limited third-party notice and attribution are explained in `ATTRIBUTION.md`.

## Next experiments and questions for expert review

1. **Resolve the reliability mechanisms before accepting a resource win.** Instrument the failing traces to separate rail truncation, bounded decision comparisons, fixed-round nonconvergence and payload errors. Derive sufficient bounds independently of failure indices. Preserve all current fixtures as regression tests, then draw a genuinely new domain for validation. A local exact identity and a lucky official packet are insufficient evidence of a reliable arithmetic circuit.
2. **Measure a narrow greedy-v2 comparator.** First test existing-window and late-only policies on a new larger denominator set. If promising, build an exact ratio-three predicate for the actual rail widths, with carries released before the existing decision logic's peak. Measure both the added Toffolis and the global width. Avoid implementing a full-width comparator at every tick without a cost estimate. No resource gain is predicted yet.
3. **Recover generic algebraic savings on the rebuilt stream.** Extend the bounded BDD fallback to memoize repeated opaque expressions while preserving soundness through garbage collection and complements. Force fallback paths in tests. The previous baseline scan found zero Toffoli saving; this extension has not been implemented or measured. Re-prove any useful specialized baseline rewrites on the changed stream rather than bypassing their guards.
4. **Use the actual width trace to choose arithmetic schedules.** The compact choice now fits under 1,234 locally while another region sets Q = 1,235. A cap-1,234 or cap-1,233 build is a cheap diagnostic next step, but one or two wires alone cannot close the present 6,281-Toffoli rounded gap at Q = 1,235. Any further fold/carry trade must be assessed against the product, not a qubit-only headline.

Specific questions for a quantum expert are whether the complement-pair encoding admits cheaper phase-clean reconstruction; whether a ratio-three decision can share existing valuation/comparison carries; whether a rigorous bounded-round rail schedule can avoid these empirical width envelopes; and whether retained-product handoffs are attractive under a physical cost model that prices Clifford routing and classical latency. Independent review of the legal-subspace invariant, measurement cleanup and conservative symbolic equality assumptions would be especially useful.

## Sources

[S1] [Pinned challenge README and scope](https://github.com/Layr-Labs/ecdsafail-challenge/blob/2120d8a20c9d277e3cfdae29639ec58a78e72e16/README.md).

[S2] [Pinned evaluator](https://github.com/Layr-Labs/ecdsafail-challenge/blob/2120d8a20c9d277e3cfdae29639ec58a78e72e16/src/bin/eval_circuit.rs), [simulator](https://github.com/Layr-Labs/ecdsafail-challenge/blob/2120d8a20c9d277e3cfdae29639ec58a78e72e16/src/sim.rs) and [resource analysis](https://github.com/Layr-Labs/ecdsafail-challenge/blob/2120d8a20c9d277e3cfdae29639ec58a78e72e16/src/circuit.rs).

[S3] [Leapfrog implementation](https://github.com/Layr-Labs/ecdsafail-challenge/blob/2120d8a20c9d277e3cfdae29639ec58a78e72e16/src/point_add/leapfrog.rs), [retained-AND attribution](https://github.com/Layr-Labs/ecdsafail-challenge/blob/2120d8a20c9d277e3cfdae29639ec58a78e72e16/src/point_add/retained_and.rs) and [canonical value analysis](https://github.com/Layr-Labs/ecdsafail-challenge/blob/2120d8a20c9d277e3cfdae29639ec58a78e72e16/src/point_add/pscan.rs).

[S4] [tarekeleter, public issue 284](https://github.com/Layr-Labs/ecdsafail-challenge/issues/284). Historical participant evidence, not reproduced here.

[S5] [rubenmarcus, public issue 380](https://github.com/Layr-Labs/ecdsafail-challenge/issues/380). Historical participant evidence, not an impossibility result.

[S6] [Pinned third-party NOTICE](https://github.com/Layr-Labs/ecdsafail-challenge/blob/2120d8a20c9d277e3cfdae29639ec58a78e72e16/NOTICE), [ZKP ECC record](https://doi.org/10.5281/zenodo.19196956) and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
