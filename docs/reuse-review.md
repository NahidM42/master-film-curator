# Existing module review

The local home/project search found no checkout named `reusable-software-modules`. A subsequent connected GitHub search resolved the private repository `NahidM42/reusable-software-modules`, default branch `main`. The full tree and repository README were reviewed; no AGENTS.md was present in that tree.

| Existing module | Decision | Reason |
| --- | --- | --- |
| CSV Record Loader | Not suitable as-is | Its contracts return claim/evidence CSV dataclasses. This project needs strict XLSX sheets, Master IDs, cross-sheet flags and read-only provenance. Header validation and BOM-aware CSV reporting are general practices, independently implemented here. |
| Persian Text Normalizer | Not suitable as-is | It deliberately preserves punctuation/spacing with NFC. Media matching requires NFKC, case folding, punctuation normalization and release-token parsing. Reusing it unchanged would violate its own preservation contract. |
| Claim Evidence Summary and Reports | Adaptation concept only | Shared reviewed data feeding several outputs is applicable, but the claim/verdict schema and artifacts are unrelated. No source implementation was copied. |
| Claim–Evidence Validator / Audit CLI | Not suitable | Their validation domain and argparse interfaces do not implement file-safety planning or Typer media workflows. |
| Deterministic Human Evaluation Engine | Not suitable | Human evaluation scoring must not be applied to immutable Rev07 scores. |

New contracts follow the repository's four-file format: MODULE_SPEC.md, REUSABLE_PROMPT.md, TESTS.md, VERSION.md. They are locally verified against synthetic media, not claimed to be approved for the user's real archive. A separate documentation branch preserves that distinction before any merge into the accepted module registry.

## Version-controlled delivery

The 40 module documents and proposed-module registry were committed to the private repository on branch `media-curator-module-specs-2026-09-30`, commit `a65222a8ad9e3ca29e0b43bf98fc968efd8459f8`.

Draft review: https://github.com/NahidM42/reusable-software-modules/pull/1

The accepted main-branch registry remains unchanged pending review. Only reusable documentation was uploaded; source workbook and media remain local.
