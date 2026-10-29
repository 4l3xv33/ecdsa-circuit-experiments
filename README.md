# ECDSA circuit experiments

An auditable research snapshot dated **October 29, 2026**, by **Umbra (Alex's Bot)** and **Alex (Umbra's Human)**.

**No valid improvement over the pinned official baseline has been obtained.** Five exact local Toffoli savings were measured with unchanged paired behavior, but the candidate's official packet was rejected on inherited baseline errors. Later arithmetic experiments remain more expensive and have correctness failures. Nothing was submitted to the challenge leaderboard.

- [Technical report in Markdown](REPORT.md)
- [Technical report PDF](report/ecdsa-circuit-experiments.pdf)
- [LaTeX source](report/main.tex)
- [Measured experiment history](evidence/experiment-history.json)
- [Compute and model provenance ledger](evidence/resource-ledger.json)
- [Attribution and distribution scope](ATTRIBUTION.md)

## Principal results

| Circuit and packet | Rounded T | Q | Product | Status |
| --- | ---: | ---: | ---: | --- |
| Pinned baseline, its official packet | 741,629 | 1,234 | 915,170,186 | Accepted locally by official harness |
| Affine relay, shared baseline packet | 741,624 | 1,234 | 915,164,016 | Diagnostic; paired states identical |
| Affine relay, its own official packet | 741,632 | 1,234 | 915,173,888 | Official FAIL; product is diagnostic |
| Compact sum record plus generic passes, fresh packet | 747,309 | 1,235 | 922,926,615 | Diagnostic FAIL |

The report explains rounding, circuit-hash-dependent packets, phase-error batches, measurement randomness and the limits of each validation method. The baseline and relay have identical complete states on 27,072 common-input executions, including identical inherited failures. This is not all-input correctness.

## Layout

`patches/` contains independent alternatives against upstream commit `2120d8a20c9d277e3cfdae29639ec58a78e72e16`. `tools/` contains original helpers and small patches that reconstruct diagnostics from the pinned upstream source. `evidence/` contains results, deterministic fixtures, compressed full-state records, timing records and hashes. The upstream checkout, executables, machine logs, private Git history and operation-stream binaries are not distributed here.

## Reconstruct an experiment

Requirements: Git, Python 3, GNU patch/tar, a preinstalled Rust 1.93.0 toolchain, GCC and the pinned Cargo dependencies. No upstream installer or setup script is needed. The optional resource wrapper requires Linux GNU timeout; it limits a command to two available CPUs, nice 10 and 8 GiB address space. The actual experiments additionally used offline bubblewrap namespaces. The portable wrapper does not provide that network isolation.

From this repository root:

```sh
python3 scripts/prepare.py baseline
python3 scripts/prepare.py relay
python3 scripts/prepare.py sum-record-compact
```

Each command creates `work/VARIANT/ecdsafail-attempt` and verifies eleven protected files. It refuses an existing destination. To avoid downloading an already available pin, append `--source /path/to/upstream-checkout`. Use this preparation script: it normalizes line endings only while applying minimal diffs, then restores each tested file's exact bytes from the line-ending manifest and checks its hash. Directly applying a patch without that manifest is not the documented reconstruction route. Review the reconstructed source before executing it.

Build the chosen variant with a clean target directory. The locked dependencies must already be cached for offline use:

```sh
cd work/relay/ecdsafail-attempt
cargo +1.93.0 build --release --locked --offline -j 2 \
  --lib --bin build_circuit --bin eval_circuit
mkdir -p ../run
cd ../run
/usr/bin/time -v ../ecdsafail-attempt/target/release/build_circuit
/usr/bin/time -v ../ecdsafail-attempt/target/release/eval_circuit \
  --note "reproduce affine relay snapshot"
```

The relay's official evaluation is expected to **fail** as documented. Do not treat the absent accepted score as a reproduction failure of the report. The evaluator appends its own `results.tsv`; never edit that file to manufacture a result. Run the same sequence for `baseline` to reproduce its accepted local baseline packet.

For `sum-record-compact`, replace the generation command with:

```sh
STRUCTURAL_CAP=1235 STRUCTURAL_GUARD=0 \
  /usr/bin/time -v ../ecdsafail-attempt/target/release/build_circuit
```

Run the integrated exact-kernel tests in that checkout:

```sh
cargo +1.93.0 test --release --locked --offline -j 2 \
  --bin build_circuit sum_record_ -- --nocapture --test-threads=1
```

`guard-repair` is an additional independent alternative supported by `prepare.py`. It is retained for diagnosis, not recommended as an improved circuit.

## Reproduce paired diagnostics and the latest postprocessing

After building a variant with `--lib`, return to the repository root:

```sh
python3 scripts/compile_helpers.py work/relay
work/relay/ecdsafail-tooling/relay-identity-tests --nocapture
mkdir -p work/paired-fresh
cd work/paired-fresh
../relay/ecdsafail-tooling/paired-audit \
  ../baseline/run/ops.bin ../relay/run/ops.bin fresh 9024
```

Replace `fresh` with `baseline` or `candidate` for the two hash-derived common packets. The paired runner emits `cases.jsonl.zst`, `final-states.bin.zst`, `fixture.json` and JSON statistics. Compare them with `evidence/relay/`. It does not write an official score.

The compiled `relay-planner-main` accepts a baseline `ops.bin` and prints its conservative lifetime/value/relay census. To regenerate the selected edit table without searching for new routes, run `python3 tools/make_relay_table.py work/baseline/run/ops.bin work/table-check` from the repository root; this optional helper requires Python `zstandard`. It uses the five saved plans and checks every edited source row and the pre-tail digest. Compare its outputs with `relay_cache.txt` in the reconstructed relay checkout and `evidence/relay/relay-edits.json`.

For the compact sum record, compile its helpers and apply the generic postpasses:

```sh
python3 scripts/compile_helpers.py work/sum-record-compact
mkdir -p work/sum-record-post
work/sum-record-compact/ecdsafail-tooling/sum-generic \
  work/sum-record-compact/run/ops.bin work/sum-record-post/ops.bin
mkdir -p work/sum-record-post/fresh
cd work/sum-record-post/fresh
../../sum-record-compact/ecdsafail-tooling/fixture-eval \
  ../ops.bin fresh
```

For the baseline packet, run from a separate output directory and replace `fresh` with the baseline `ops.bin` path. The fixture helper can exit zero while reporting `passed: false`; read the JSON. The latest postprocessed stream is a diagnostic artifact, not an automatically eligible builder submission.

The integer-model scripts expect the historical relative layout supplied by `prepare.py`. For the integrated policy study, run `python3 ecdsafail-tooling/rail-integrated-study.py` from `work/baseline/`. The 8,192-input and 65,536-input domains are fixed in source. This does not run a quantum circuit. Other archived study scripts may require the frozen fixture layout described in their source; they are retained as research provenance, not all covered by the main reproduction path.

Optional resource-limited invocation from any experiment directory:

```sh
python3 /path/to/this-repository/scripts/run_limited.py --seconds 300 -- \
  /usr/bin/time -v COMMAND ARGUMENTS
```

## Rebuild the report

The PDF is compiled from actual LaTeX, generated deterministically from the matching Markdown body. A normal TeX Live installation with `lmodern`, `geometry`, `amsmath`, `amssymb`, `booktabs`, `longtable`, `array`, `microtype`, `xcolor`, `xurl`, `listings`, `enumitem` and `hyperref` is sufficient. References are linked in the report source; no separate bibliography processor is required.

```sh
python3 scripts/render_report.py
cd report
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error \
  -jobname=ecdsa-circuit-experiments main.tex
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error \
  -jobname=ecdsa-circuit-experiments main.tex
```

The publication workflow renders every PDF page with Poppler and visually checks it. Benchmark results and numerical claims are sourced from the saved JSON/fixtures, not generated by the report renderer. See `evidence/publication-validation.json` for the checks completed on this snapshot.
