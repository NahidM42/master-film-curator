# Reusable Media Curator Modules

Version 0.1.0. Verified with synthetic media and the public 60-record read-only workbook fixture; private real-archive acceptance remains pending. Each directory follows the private reusable-module repository format.

| Module | Contract |
| --- | --- |
| Local Curator Configuration and State | [media-config-state](media-config-state/MODULE_SPEC.md) |
| Read-only Rev07 Excel Catalog Import | [media-rev07-catalog](media-rev07-catalog/MODULE_SPEC.md) |
| Media Filename and Episode Parser | [media-name-series-parser](media-name-series-parser/MODULE_SPEC.md) |
| Read-only Multi-root Media Scanner | [media-readonly-scanner](media-readonly-scanner/MODULE_SPEC.md) |
| Confidence Matching and Persistent Review | [media-confidence-matcher](media-confidence-matcher/MODULE_SPEC.md) |
| ffprobe Video Metadata and Resolution Classes | [media-ffprobe-quality](media-ffprobe-quality/MODULE_SPEC.md) |
| Classification and Safe File Operation Planner | [media-safe-operation-planner](media-safe-operation-planner/MODULE_SPEC.md) |
| Verified No-overwrite Operations and Rollback | [media-journaled-operations](media-journaled-operations/MODULE_SPEC.md) |
| Media Inventory and Operation Reports | [media-inventory-reports](media-inventory-reports/MODULE_SPEC.md) |
| Typer CLI and Optional Textual Review | [media-cli-review-ui](media-cli-review-ui/MODULE_SPEC.md) |
