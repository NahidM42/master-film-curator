# Master Film Curator

Master Film Curator is a safety-first Python application for catalog-driven film and series archive curation. It combines read-only Excel catalog ingestion, confidence-based matching, `ffprobe` media analysis, human review, dry-run operation planning, verified no-overwrite file operations, audit trails, and rollback/recovery.

The public repository is designed to run against a **fully synthetic 60-record catalog**. Private archive paths and the user's real workbook are intentionally kept out of version control.

## Overview

The application turns a trusted catalog into an auditable organization workflow without treating filenames as certain identities. It indexes local media read-only, ranks candidate matches, requires review for ambiguous cases, records quality metadata, builds an immutable plan, and performs media changes only through an explicit `apply` command.

The pre-public-cleanup baseline recorded **70 automated tests passing**. This branch migrates those tests and demonstrations to the synthetic catalog; GitHub Actions re-runs the suite before public release.

## Why This Project Exists

Large media archives combine several failure-prone tasks: identifying files, distinguishing same-title works, handling multiple encodes, preserving series structure and sidecars, inspecting resolution, and moving data across filesystems. A useful curator therefore needs more than renaming rules: it needs uncertainty handling, review gates, collision protection, verifiable writes, and recovery evidence.

## Key Features

- Read-only XLSX catalog ingestion with stable Master IDs and independent cross-sheet flags
- Confidence-based matching with explicit ambiguity handling and persistent human review
- Multi-root, read-only media scanning
- `ffprobe` metadata and resolution classification
- SQLite application state and audit events
- Typer/Rich CLI plus optional Textual review UI
- Dry-run planning before any media mutation
- SHA-256 verification by default
- No-overwrite publication and collision protection
- Journaled file operations and rollback/recovery workflow
- Conservative handling of sidecars, extras, multiple encodes, and uncertain series episodes
- Reproducible synthetic demonstration data for public use

## Safety Model

Routine commands—`doctor`, `import-catalog`, `scan`, `match`, `quality`, `review`, `plan`, `report`, and `status`—do not rename or delete media. The explicit `apply` command is the mutation boundary and requires approval. Existing destinations are never silently replaced. Cross-filesystem copies are verified before any optional source deletion, and operations are journaled for conservative rollback.

See [docs/safety.md](docs/safety.md) for invariants, crash semantics, filesystem assumptions, and recovery limits.

## Architecture

The Python package is `master_film_curator`. Core modules cover catalog ingestion, configuration/state, read-only scanning, filename/series parsing, confidence matching, `ffprobe` analysis, operation planning, verified execution/rollback, reporting, and CLI/TUI review.

See [docs/architecture.md](docs/architecture.md) for the component and data-flow overview.

## Workflow

```text
Synthetic/private catalog
        ↓
import-catalog
        ↓
      scan
        ↓
      match
        ↓
     quality
        ↓
     review
        ↓
      plan
        ↓
     report
        ↓
explicit apply approval
        ↓
journal + verification
        ↓
rollback/recovery if needed
```

## Installation

Requirements:

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- FFmpeg/`ffprobe` for media-quality analysis and the full integration demo

```bash
uv sync --extra tui
sudo apt update
sudo apt install ffmpeg
uv run film-curator --help
```

The base application can be installed without Textual using `uv sync`; CLI review remains available.

## Quick Start

The tracked `config.yaml` is public-safe and targets the generated 60-record sample catalog. Generate the sample once after cloning:

```bash
uv run python scripts/generate_sample_catalog.py
uv run film-curator import-catalog
uv run film-curator status
```

For a private archive, copy the public config to the ignored local file and edit only the local copy:

```bash
cp config.yaml config.local.yaml
uv run film-curator --config config.local.yaml doctor
```

Keep the real workbook, mounted-drive paths, databases, reports, and logs out of Git.

## CLI

Recommended non-destructive sequence:

```bash
uv run film-curator doctor
uv run film-curator import-catalog
uv run film-curator scan
uv run film-curator match
uv run film-curator quality
uv run film-curator review
uv run film-curator plan
uv run film-curator report
uv run film-curator status
```

To use another configuration, place `--config` before the command:

```bash
uv run film-curator --config config.local.yaml scan
```

Mutation is separate and explicit:

```bash
uv run film-curator apply --plan PLAN_ID --dry-run
uv run film-curator apply --plan PLAN_ID
```

Do not run a real `apply` until the saved Plan has been reviewed.

## Synthetic Demo Dataset

`scripts/generate_sample_catalog.py` creates:

```text
sample-data/Rev07_Sample_Catalog_60.xlsx
```

The workbook contains **exactly 60 fictional primary catalog records** and uses the same importer-facing schema as the private Rev07 workflow. It includes films, series hints, multiple years, repeated and near-duplicate titles, all tiers, all viewing-priority levels, independent cross-sheet flags, and matching/reporting edge cases. It was designed from scratch for public demonstration and is not an anonymized copy of the user's archive.

The workbook inspection summary is in [docs/excel-inspection.md](docs/excel-inspection.md).

## Testing

Local verification commands:

```bash
uv run python scripts/generate_sample_catalog.py
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
uv run film-curator --help
```

With FFmpeg installed, the generated-library integration path can also be exercised:

```bash
uv run python scripts/run_fake_library.py \
  --output ./demo-output \
  --ffmpeg ffmpeg \
  --ffprobe ffprobe
```

The integration script creates its own media fixtures in a new directory, performs dry-run and synthetic-only Apply/rollback checks, and never accepts a real archive root.

## Project Structure

```text
.
├── config.yaml
├── docs/
├── sample-data/
├── scripts/
├── src/master_film_curator/
├── tests/
├── pyproject.toml
└── uv.lock
```

Private/local state belongs in ignored files such as `config.local.yaml`, `.state/`, `reports/`, and `logs/`.

## Known Limitations

- Filename matching is deliberately heuristic; it is not a global movie-identification service.
- Alternate-language titles and unusual release naming can require manual review.
- Series completeness cannot be inferred from the catalog.
- Resolution classification is not perceptual-quality scoring or upscaling detection.
- The safety design is not an atomic distributed transaction across multiple filesystems.
- NTFS/exFAT mount behavior and physical drive disconnects require a small user-approved pilot before large real-archive operations.
- No real archive Apply is part of the public demonstration.

## Documentation

- [Architecture](docs/architecture.md)
- [Safety and recovery](docs/safety.md)
- [Synthetic Excel inspection](docs/excel-inspection.md)
- [Validation record](docs/validation.md)
- [Reusable module contracts](docs/modules/README.md)

## Persian Documentation

برنامهٔ محلی Python برای مدیریت ایمن آرشیو فیلم و سریال، با Excel Rev07 به‌عنوان مرجع قطعی طبقه‌بندی. امتیازها، Tier و اولویت‌ها تغییر نمی‌کنند. برنامه به سرویس آنلاین یا کلید API نیاز ندارد.

**وضعیت:** نسخهٔ اولیهٔ قابل اجرا و آزموده‌شده روی آرشیو ساختگی. هیچ Apply روی فایل‌های واقعی کاربر انجام نشده است. مسیرهای آرشیو عمداً در تنظیمات خالی هستند.

## نصب در Ubuntu / WSL2

```bash
uv sync --extra tui
sudo apt update
sudo apt install ffmpeg
uv run film-curator --help
```

Python 3.12 یا جدیدتر لازم است. برای نصب بدون Textual از `uv sync` استفاده کنید؛ تمام قابلیت‌های مرور از CLI هم در دسترس‌اند. `ffprobe` باید در PATH باشد یا مسیر فایل اجرایی آن در `config.yaml` مشخص شود. نبود آن مانع `quality` و Apply واقعی است؛ اسکن و تهیهٔ Plan همچنان ممکن است.

در محیط توسعهٔ فعلی، نسخهٔ مستقل آزمایشی در `.state/linux/ffprobe` و `.state/linux/ffmpeg` دریافت شده است. برای استفادهٔ موقت می‌توانید PATH را تنظیم کنید؛ این فایل‌ها وارد Git نشده‌اند:

```bash
export PATH="$PWD/.state/linux:$PATH"
```

## تنظیمات

[config.yaml](config.yaml) را ویرایش کنید. مسیرهای نسبی نسبت به محل همان فایل تفسیر می‌شوند، نه پوشهٔ جاری Terminal.

```yaml
sources:
  - /path/to/movies
  - /path/to/series
destination_root: /path/to/curated-media
excel_path: ./sample-data/Rev07_Sample_Catalog_60.xlsx
database_path: ./.state/curator.sqlite3
reports_root: ./reports
logs_root: ./logs
expected_catalog_count: 60
classification:
  primary: viewing_priority
  secondary: channel_tier
operation_mode:
  dry_run: true
verification_mode: sha256
matching:
  auto_accept: 95
  review_threshold: 70
  ambiguity_margin: 5
quality:
  min_1080_width: 1800
  min_1080_height: 780
  nominal_1080_width: 1900
ffprobe: ffprobe
max_path_length: 240
max_component_length: 110
```

برای ترتیب معکوس، `classification.strategy: tier_then_priority` را تعیین کنید. مقادیر ناشناختهٔ تنظیمات رد می‌شوند. `operation_mode.dry_run: false` اجازهٔ ضمنی اجرای عملیات نمی‌دهد؛ تنها فرمان صریح `apply` همراه تأیید می‌تواند رسانه‌ها را تغییر دهد.

## گردش کار ایمن

```bash
uv run film-curator doctor
uv run film-curator import-catalog
uv run film-curator scan
uv run film-curator match
uv run film-curator quality
uv run film-curator review
uv run film-curator plan
uv run film-curator report
uv run film-curator status
```

برای تنظیمات متفاوت، `--config` را **قبل از فرمان** بیاورید:

```bash
uv run film-curator --config /path/to/config.yaml scan
```

`scan` فقط رسانه‌ها را می‌خواند؛ دادهٔ برنامه در SQLite ثبت می‌شود. پوشهٔ مقصد نیز هنگام وجود، برای تشخیص اجرای مجدد اسکن می‌شود. مسیرهای symlink دنبال نمی‌شوند. قطع Drive باعث کنار گذاشتن رکوردهای آن از موجودی فعال می‌شود و در نتیجهٔ اسکن گزارش می‌گردد.

`plan` یک شناسه و خلاصه می‌دهد. مسیرهای کامل پیشنهادی در SQLite و گزارش‌های `move_plan.csv` و `rename_plan.csv` قابل بررسی‌اند. تغییر catalog، scan، match، quality یا تصمیم دستی، Planهای قبلی را stale می‌کند؛ پس Plan را در پایان بسازید.

## مرور دستی

```bash
uv run film-curator review --interactive
uv run film-curator review --tui
uv run film-curator review --file-id 12 --action accept --master-id 545
uv run film-curator review --file-id 13 --action reject
uv run film-curator review --file-id 14 --action not_in_catalog
uv run film-curator review --file-id 15 --action ignore
```

می‌توانید هر Master ID معتبر را انتخاب کنید. `reject` یعنی رد تطبیق این فایل و توقف تا تصمیم جدید؛ فقط حذف یکی از پیشنهادها نیست. `ignore` در اسکن‌های بعدی همین مسیر باقی می‌ماند. تغییر محتوای فایل، تأییدهای قبلی را باطل می‌کند. برای لغو تصمیم، همان فایل را دوباره با عمل مناسب review کنید.

تطبیق عنوان و سال دقیق ۱۰۰، اختلاف یک سال ۹۷ و عنوان دقیق همراه کارگردان ۹۶ است. عنوان بدون سال و تطبیق fuzzy به‌طور پیش‌فرض نیاز به مرور دارند. نزدیکی امتیاز دو پیشنهاد مانع پذیرش خودکار است. چند encode از یک فیلم یا یک اپیزود، `multiple_candidates` می‌گیرند. اپیزودهای متفاوت یک سریال تکراری محسوب نمی‌شوند. پذیرش دستی چند نسخه، شناسهٔ نسخه را در نام حفظ می‌کند.

## Apply؛ فقط پس از بررسی Plan

```bash
uv run film-curator apply --plan PLAN_ID --dry-run
uv run film-curator apply --plan PLAN_ID
```

فرمان دوم خلاصه را نشان می‌دهد و تأیید صریح می‌خواهد. `--yes` همان تأیید صریح برای اجرای غیرتعاملی است. Apply شناسهٔ عملیات را برمی‌گرداند.

در جابه‌جایی میان فایل‌سیستم‌ها، پیش‌فرض فقط کپی تأییدشده است و مبدأ باقی می‌ماند. حذف مبدأ پس از کپی بین دو Drive نیاز به پرچم مستقل دارد:

```bash
uv run film-curator apply --plan PLAN_ID --delete-source-after-verify
```

در یک فایل‌سیستم، Move تأییدشده مبدأ را پس از انتشار و تأیید مقصد حذف می‌کند. برای سازگاری و ایمنی، این نسخه حتی Move هم‌درایو را با کپی موقت و تأیید انجام می‌دهد؛ فضای آزاد برای کل Plan لازم است. اندازه و زمان/شناسهٔ فایل دوباره بررسی می‌شوند. انتشار مقصد با روش atomic و no-replace انجام می‌شود. هر collision اجرای Plan را متوقف می‌کند؛ حذف و replace خودکار وجود ندارد.

`verification_mode` یکی از `size`، `quick_hash` و `sha256` است. `quick_hash` سه بخش از فایل را می‌خواند و تضمین هش کامل ندارد؛ برای آرشیو واقعی `sha256` پیشنهاد می‌شود. جهت Rollback، اثرانگشت SHA-256 مقصد همیشه ثبت می‌گردد.

## Rollback و بازیابی

```bash
uv run film-curator rollback OPERATION_ID
uv run film-curator rollback OPERATION_ID --execute
```

اولی فقط ایمنی بازگردانی را بررسی می‌کند؛ دومی تأیید می‌گیرد. اگر مبدأ با فایل دیگری اشغال شده، مقصد تغییر کرده یا مالکیت فایل پس از قطع ناگهانی مشخص نیست، عملیات مربوطه دست‌نخورده باقی می‌ماند و دلیل گزارش می‌شود. پوشه‌های خالی حذف نمی‌شوند.

ژورنال معتبر هر عملیات:

```text
logs/<operation-id>/rollback_manifest.json
logs/operations.jsonl
```

اجرای ناموفق در میانهٔ Plan، کل مجموعه را تراکنش اتمی نمی‌کند؛ عملیات انجام‌شده در ژورنال باقی می‌مانند و قابل بررسی/بازگردانی‌اند. برای جزئیات بازیابی پس از قطع برق یا kill، [ملاحظات ایمنی](docs/safety.md) را بخوانید.

## پوشه‌ها و کیفیت

```text
01_Essential/S/Lanterns at Noon (1966) — Mira Voss/
90_Quality_Review/Below_1080/01_Essential/S/...
90_Quality_Review/Above_1080_4K/01_Essential/S/...
90_Quality_Review/Unknown_Resolution/01_Essential/S/...
```

رزولوشن از stream ویدئو خوانده می‌شود؛ 1920×800 کلاس 1080 است. 4K کیفیت بد برچسب نمی‌گیرد. پرچم‌های سلیقه و کانال فقط در دیتابیس و گزارش هستند؛ کپی فیزیکی یا symlink collection تولید نمی‌شود.

هر فیلم پوشهٔ مستقل دارد. نام فایل `Title (Year) — Director.ext` است؛ همهٔ کارگردان‌ها تا بودجهٔ مسیر حفظ می‌شوند. نام‌های ناسازگار با Windows پاک‌سازی و نام‌های بلند با hash پایدار کوتاه می‌شوند؛ تغییرات در Plan ثبت می‌گردند.

سریال به `Series (Year) — Creator/Season 01/Series - S01E01.ext` می‌رود. نسخهٔ فعلی عنوان اپیزود را از وب حدس نمی‌زند. اپیزودهای چندبخشی و شماره‌های نامطمئن مسدود می‌شوند، حتی اگر تطبیق عنوان را دستی پذیرفته باشید.

Subtitle و NFO با basename قابل‌انتساب، پوستر عمومی پوشهٔ تک‌فیلمی و Extras در پوشهٔ اختصاصی همراه رسانه می‌روند. زبان مشخص حفظ می‌شود؛ زبان نامشخص پسوند قابل‌ردیابی می‌گیرد. همراه مشترک یا زیرنویس غیرقابل‌انتساب، همان bundle را مسدود می‌کند؛ پس فایل‌ها را دستی در پوشه‌های روشن قرار دهید و Plan تازه بسازید.

## Excel و گزارش‌ها

[گزارش بررسی Excel](docs/excel-inspection.md) و [دادهٔ بررسی کامل](docs/excel-inspection.json) ساختار هشت شیت، تعدادها و عنوان‌های تکراری را ثبت می‌کنند. شیت اصلی `Rev07_Channel_Value_Ranking` و ستون Tier برابر `Rev07 Tier` است. چهار شیت پرچم با Master ID متصل می‌شوند. فایل read-only باز می‌شود؛ محتوای خام سطرها نیز ذخیره می‌گردد.

هر `report` پوشهٔ زمان‌دار تازه می‌سازد و همهٔ این خروجی‌ها را دارد:

- `library_inventory.csv`, `matched.csv`, `missing_from_library.csv`, `unmatched_on_disk.csv`
- `ambiguous_matches.csv`, `duplicate_candidates.csv`
- `below_1080.csv`, `above_1080_4k.csv`, `unknown_resolution.csv`
- `rename_plan.csv`, `move_plan.csv`, `operation_summary.json`, `rollback_manifest.json`, `summary.md`

Missing یعنی «تطبیق تأییدشده در موجودی در دسترس ندارد». ستون pending نشان می‌دهد چند فایل هنوز در مرور هستند. Drive آفلاین و سریال ناقص را نباید با نبود قطعی اثر اشتباه گرفت. CSVها UTF-8 BOM دارند و فرمول‌های بالقوهٔ Excel در رشته‌های ورودی escape می‌شوند.

## آزمون و نمونهٔ سرتاسری

```bash
uv run pytest
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run python scripts/run_fake_library.py --output ./demo-output --ffmpeg ffmpeg --ffprobe ffprobe
```

اسکریپت فقط پوشهٔ خروجی **جدید** می‌پذیرد و همهٔ ویدئوها را خودش تولید می‌کند؛ مسیر آرشیو واقعی دریافت نمی‌کند. Excel صرفاً خوانده می‌شود. Import، scan، match، ffprobe، report، Apply آزمایشی، اجرای دوم و Rollback بررسی می‌شوند. اگر FFmpeg موجود نباشد، تست واقعی آن با دلیل skip می‌شود؛ برای اعتبارسنجی کامل باید نصب باشد.

ساختار ماژولار در [Architecture](docs/architecture.md)، نتیجهٔ اعتبارسنجی در [Validation](docs/validation.md) و قراردادهای بازاستفاده در [docs/modules](docs/modules/README.md) قرار دارد.
