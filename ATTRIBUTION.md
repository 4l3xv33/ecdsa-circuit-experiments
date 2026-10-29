# Attribution and distribution scope

The upstream benchmark is [Layr-Labs/ecdsafail-challenge](https://github.com/Layr-Labs/ecdsafail-challenge), pinned to `2120d8a20c9d277e3cfdae29639ec58a78e72e16`.

No repository-wide license file was present at that revision. Its `NOTICE` identifies only `src/circuit.rs`, `src/sim.rs` and `src/weierstrass_elliptic_curve.rs` as reused under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) from Tanuj Khattar et al., [ZKP ECC](https://doi.org/10.5281/zenodo.19196956), with the patched [GitHub mirror](https://github.com/tanujkhattar/zkp_ecc). The benchmark README additionally credits Google's research and Kirk Baird's review. This snapshot does not assert a broader license for upstream files.

Accordingly, this repository distributes experiment deltas and original research artifacts, not an upstream checkout, its Git history, its executable binaries or its unchanged evaluator source. Fetch the pinned upstream separately to reconstruct experiments. Files under `tools/derived` are patches against the named upstream files. The integer models are explanatory ports of the pinned walk, and their relationship to upstream is recorded in the report. No blanket license is applied to inherited material.

Retained-AND caching is credited to **MonitSharma** by upstream `src/point_add/retained_and.rs`. Canonical Boolean value numbering follows upstream `pscan.rs`. Our relay contribution extends storage lifetimes using affine clearing and handoffs. The sum-budget record, its integration and the experiments described in the report are this investigation's additions; novelty beyond this investigation has not been established.

Public issue reports by **tarekeleter** ([issue 284](https://github.com/Layr-Labs/ecdsafail-challenge/issues/284)) and **rubenmarcus** ([issue 380](https://github.com/Layr-Labs/ecdsafail-challenge/issues/380)) supplied leads on workspace floors, common-input testing and approximation tradeoffs. Their historical scores were not reproduced here. This report neither claims their results nor implies their endorsement.
