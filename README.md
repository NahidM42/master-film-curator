# Media Library Curator

برنامهٔ محلی Python برای مدیریت ایمن آرشیو فیلم و سریال، با Excel Rev07 به‌عنوان مرجع قطعی طبقه‌بندی. امتیازها، Tier و اولویت‌ها تغییر نمی‌کنند. برنامه به سرویس آنلاین یا کلید API نیاز ندارد.

**وضعیت:** نسخهٔ اولیهٔ قابل اجرا و آزموده‌شده روی آرشیو ساختگی. هیچ Apply روی فایل‌های واقعی کاربر انجام نشده است. مسیرهای آرشیو عمداً در تنظیمات خالی هستند.

## نصب در Ubuntu / WSL2

```bash
uv sync --extra tui
sudo apt update
sudo apt install ffmpeg
uv run media-curator --help
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
  - ./generated-library/movies
  - ./generated-library/series
destination_root: ./curated-media
excel_path: ./private-catalog.xlsx
database_path: ./.state/curator.sqlite3
reports_root: ./reports
logs_root: ./logs
expected_catalog_count: 570
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
uv run media-curator doctor
uv run media-curator import-catalog
uv run media-curator scan
uv run media-curator match
uv run media-curator quality
uv run media-curator review
uv run media-curator plan
uv run media-curator report
uv run media-curator status
```

برای تنظیمات متفاوت، `--config` را **قبل از فرمان** بیاورید:

```bash
uv run media-curator --config /path/to/config.yaml scan
```

`scan` فقط رسانه‌ها را می‌خواند؛ دادهٔ برنامه در SQLite ثبت می‌شود. پوشهٔ مقصد نیز هنگام وجود، برای تشخیص اجرای مجدد اسکن می‌شود. مسیرهای symlink دنبال نمی‌شوند. قطع Drive باعث کنار گذاشتن رکوردهای آن از موجودی فعال می‌شود و در نتیجهٔ اسکن گزارش می‌گردد.

`plan` یک شناسه و خلاصه می‌دهد. مسیرهای کامل پیشنهادی در SQLite و گزارش‌های `move_plan.csv` و `rename_plan.csv` قابل بررسی‌اند. تغییر catalog، scan، match، quality یا تصمیم دستی، Planهای قبلی را stale می‌کند؛ پس Plan را در پایان بسازید.

## مرور دستی

```bash
uv run media-curator review --interactive
uv run media-curator review --tui
uv run media-curator review --file-id 12 --action accept --master-id 545
uv run media-curator review --file-id 13 --action reject
uv run media-curator review --file-id 14 --action not_in_catalog
uv run media-curator review --file-id 15 --action ignore
```

می‌توانید هر Master ID معتبر را انتخاب کنید. `reject` یعنی رد تطبیق این فایل و توقف تا تصمیم جدید؛ فقط حذف یکی از پیشنهادها نیست. `ignore` در اسکن‌های بعدی همین مسیر باقی می‌ماند. تغییر محتوای فایل، تأییدهای قبلی را باطل می‌کند. برای لغو تصمیم، همان فایل را دوباره با عمل مناسب review کنید.

تطبیق عنوان و سال دقیق ۱۰۰، اختلاف یک سال ۹۷ و عنوان دقیق همراه کارگردان ۹۶ است. عنوان بدون سال و تطبیق fuzzy به‌طور پیش‌فرض نیاز به مرور دارند. نزدیکی امتیاز دو پیشنهاد مانع پذیرش خودکار است. چند encode از یک فیلم یا یک اپیزود، `multiple_candidates` می‌گیرند. اپیزودهای متفاوت یک سریال تکراری محسوب نمی‌شوند. پذیرش دستی چند نسخه، شناسهٔ نسخه را در نام حفظ می‌کند.

## Apply؛ فقط پس از بررسی Plan

```bash
uv run media-curator apply --plan PLAN_ID --dry-run
uv run media-curator apply --plan PLAN_ID
```

فرمان دوم خلاصه را نشان می‌دهد و تأیید صریح می‌خواهد. `--yes` همان تأیید صریح برای اجرای غیرتعاملی است. Apply شناسهٔ عملیات را برمی‌گرداند.

در جابه‌جایی میان فایل‌سیستم‌ها، پیش‌فرض فقط کپی تأییدشده است و مبدأ باقی می‌ماند. حذف مبدأ پس از کپی بین دو Drive نیاز به پرچم مستقل دارد:

```bash
uv run media-curator apply --plan PLAN_ID --delete-source-after-verify
```

در یک فایل‌سیستم، Move تأییدشده مبدأ را پس از انتشار و تأیید مقصد حذف می‌کند. برای سازگاری و ایمنی، این نسخه حتی Move هم‌درایو را با کپی موقت و تأیید انجام می‌دهد؛ فضای آزاد برای کل Plan لازم است. اندازه و زمان/شناسهٔ فایل دوباره بررسی می‌شوند. انتشار مقصد با روش atomic و no-replace انجام می‌شود. هر collision اجرای Plan را متوقف می‌کند؛ حذف و replace خودکار وجود ندارد.

`verification_mode` یکی از `size`، `quick_hash` و `sha256` است. `quick_hash` سه بخش از فایل را می‌خواند و تضمین هش کامل ندارد؛ برای آرشیو واقعی `sha256` پیشنهاد می‌شود. جهت Rollback، اثرانگشت SHA-256 مقصد همیشه ثبت می‌گردد.

## Rollback و بازیابی

```bash
uv run media-curator rollback OPERATION_ID
uv run media-curator rollback OPERATION_ID --execute
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
01_Essential/S/Persona (1966) — Ingmar Bergman/
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
