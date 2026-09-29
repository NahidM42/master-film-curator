def write_summary(path, summary):
    lines = [
        "# Media Library Curator",
        "",
        "Local inventory report. Excel scores and tiers are preserved verbatim.",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in [
        "catalog_count",
        "present_media",
        "offline_or_missing_files",
        "confirmed_files",
        "missing_unconfirmed_titles",
        "ambiguous_files",
    ]:
        lines.append(f"| {key.replace('_', ' ')} | {summary[key]} |")
    lines += [
        "",
        "Missing means no confirmed match in the latest available inventory. Pending review and offline drives "
        "can explain absence; do not treat this report as proof that a title was never acquired.",
        "",
        "Distinct episodes do not establish season completeness; the catalog has no episode inventory.",
        "",
        "Resolution is measured from video stream dimensions, not perceptual quality or proof of the original source.",
        "",
        "Plans do not modify media. Review collisions and ambiguous matches before explicitly applying a plan.",
        "",
        f"Latest plan: `{summary['latest_plan_id']}` ({summary['latest_plan_status']}).",
        "",
        "The authoritative rollback journal is logs/<operation-id>/rollback_manifest.json. "
        "This report contains a database snapshot of operation manifests.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
