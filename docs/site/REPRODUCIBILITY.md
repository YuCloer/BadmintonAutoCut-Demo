# Reproducibility and evidence provenance

This repository publishes a source-attributed visual record, not the original research dataset. The [evidence manifest](evidence-manifest.json) identifies each public figure, model/stage, experiment state, source/time binding where applicable, supported claim, and limitation.

## What was reused

- The four-source TrackNet raw scatter is the original high-resolution PNG. Its source rows and per-source counts are recorded in the manifest. The adjacent report heatmap is a distinct aggregate-cell figure.
- The Court, Pose, failure, start, and midpoint examples reuse existing high-resolution model screenshots without redraw.
- The report probability timeline, categorical GT/M6 timeline, boundary profiles, model comparison, heatmap, and ablation are original report figures copied as image files. `RESEARCH_REPORT.html` is the original self-contained report with inline image bytes; it links to this page for the public package scope.
- Four extra stills were individually extracted from existing 1920×1080 analysis renders: samples 285, 330, and 368 for source 26100302, and sample 16,701 for source 26100304. Each was accepted only when source ID, output-frame index, native PTS, native frame index, time base, and full-source PTS verification matched the frozen frame map and video manifest. No video range was decoded for this package.

## What is not included

The bundle contains no source videos, proxies, model checkpoints, raw cache, full candidate tables, GT annotation files, identity data, or local viewer payloads. It therefore cannot reproduce the numerical evaluation or rerun inference from this public repository alone. The report metrics are preserved as cited research outputs, not recomputed from the displayed images.

The Oct 3 four-source study, the Aug 7 `260807-92` Court checkpoint, and the Oct 13 archived ablation remain separate experiments. Their images must not be combined into one cohort or read as proof of cross-date generalization. Editorial intervals are editing references and do not establish physical shuttle or Hit truth.
