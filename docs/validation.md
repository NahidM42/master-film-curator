# Verification record — v0.1.0

Verified 2026-09-30 (Asia/Tehran), Python 3.12.13 in WSL/Linux. All tests use temporary/generated media; the supplied workbook is read-only. No real user media source roots have been configured, scanned, moved or renamed.

## Final checks

- `uv sync --extra tui`: successful reproducible editable installation; `uv.lock` checked in.
- `pytest -q --junitxml=docs/test-results.xml`: **70 passed**, no skipped tests in this environment; final recorded run 9.68 seconds.
- `ruff check src tests scripts`: passed.
- `ruff format --check src tests scripts`: verified at handoff.
- Pre-rename validation — installed `media-curator --help`: all eleven requested commands present.
- Pre-rename validation — installed `media-curator import-catalog`: **570** imported to the local application state.
- Pre-rename validation — `media-curator --config demo-output/config.yaml doctor`: all checks passed using explicitly configured local ffprobe.
- `uv build`: source distribution and wheel built successfully. CLI and report modules imported successfully directly from the built wheel.

The standalone synthetic demo imported 570 records, indexed 11 videos, confirmed 6 video matches, held 2 duplicate encodes and 1 ambiguous title, identified 1 unknown title and 1 extra. Real ffprobe read 10 valid clips; the deliberately invalid clip produced a recorded Unknown error. The Plan contained 9 files (including subtitle, poster and extra), with one below-1080 movie, one above-1080 movie, one Unknown movie and one series folder. Three uncertain files were excluded.

Apply completed on synthetic media only. The second scan/match/quality/plan produced **0 operations**. Rollback completed and every original file's SHA-256 matched the pre-run value. Local evidence: `demo-output/acceptance-result.json`; reports and journals are retained under that directory but ignored by Git. Test-case evidence is in `docs/test-results.xml`.

## Acceptance mapping

| Criterion | Evidence |
| --- | --- |
| 1. 570-row import | Real-workbook test checks count, IDs, flags and unchanged bytes |
| 2. Multiple roots | Scanner tests and two-root generated library |
| 3. Confidence matching | Exact, ±1 year, fuzzy, wrong-year and same-title tests |
| 4. Ambiguity excluded | Matcher and Plan tests; synthetic Shame remains untouched |
| 5. Missing titles | CSV assertions and 565 unconfirmed catalog titles in demo |
| 6. Unknown disk files | Unknown fixture remains in place and is reported |
| 7. ffprobe | Actual generated streams and invalid-video error |
| 8. CinemaScope 1080 | 1920×800 unit test and real ffprobe clip |
| 9. Quality separation | Below, above and Unknown Plan destinations |
| 10. Rev07 classification | Priority/tier and alternate strategy tests |
| 11. Canonical movies | Safe character, reserved name, long path and director tests |
| 12. Series preserved | Episode parser, uncertain-series block and two-episode E2E |
| 13. Sidecars | Language, unknown language, poster and shared-owner handling |
| 14. Non-destructive preview | Original bytes/mtime and missing output roots checked |
| 15. No overwrite | Existing path, case alias and atomic-publication race tests |
| 16. Audit | SQLite event trail, JSONL and per-operation journal |
| 17. Cross-device verification | Simulated filesystem boundary; copy with/without delete flag |
| 18. Rollback manifest | Created before mutation, updated at each phase, inspected in tests |
| 19. Idempotency | Already-applied Plan, second empty Plan, long names and retained originals |
| 20. Tests pass | 70 passing tests plus standalone demo and package build |

## Boundaries of verification

Real ffprobe and actual local file operations were tested. A different filesystem boundary was simulated in unit tests; physical Windows/external-drive unplug, NTFS/exFAT mount options, and power-loss recovery were **not** tested on user drives. Hard crashes can leave a journaled staging file or uncertain phase. The safety document defines conservative manual recovery; it does not claim an impossible atomic whole-library transaction.

The optional TUI was exercised using Textual's headless pilot. Base runtime imports no Textual; if the optional dependency is absent, only the TUI test skips. The FFmpeg integration test skips with an explicit installation reason when binaries are unavailable. Install both to reproduce the full 70-test run without skips.

Module contract documentation is proposed in a separate branch of the private reusable-module repository. Source code and workbook remain local unless separately published by the user.
