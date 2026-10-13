# BadmintonAutoCut Demo v0.1

**[Live Interactive Demo](https://yucloer.github.io/BadmintonAutoCut-Demo/) · [Source Code](https://github.com/YuCloer/BadmintonAutoCut-Demo) · [Research Results](#research-results)**

A small static research viewer for aggregate badminton Rally boundary metrics. Open `index.html` directly in a browser or use the hosted demo; the page runs in the browser with local CSS and JavaScript and needs no build step, model, or third-party runtime service.

## Research Results

The page compares two Player + TrackNet research arms on **four videos from one recording date**. The reference intervals are human-edited editorial timelines; they are **not physical LIVE/DEAD truth**. A complete match requires both predicted boundaries to fall within ±0.5 seconds of an editorial interval. The page shows aggregate counts and error tradeoffs only; it has no per-video rows, source identifiers, frame timeline, annotation data, media, or checkpoint.

The tail-safe arm matched 79 of 148 editorial intervals, with 59.85% precision and 53.38% recall. It lost 164.33 seconds of editorial LIVE time and retained 62.85 seconds of editorial DEAD time. The unguarded context arm matched 82 of 148, with 61.65% precision and 55.41% recall; it lost 175.60 seconds LIVE and retained 51.12 seconds DEAD. Both are research results, and the tradeoff is shown without selecting a production winner.

Formal CurrentCourt admission, production Rally, KeepTimeline, and export acceptance remain unearned. The separate two-date replication did not establish generalization. The internal research report and all per-source detail are not part of this repository.

This repository contains the static viewer and aggregate values only. The core inference implementation, private models, and weights are not included. This is a research showcase, not a production-ready automatic editor.

## Static checks

With Python 3.10+ standard library, run:

```powershell
python -m unittest discover -s tests -v
```

The check verifies the positive allowlist, local-only assets, privacy exclusions, and aggregate-only values. It does not inspect any source project files or media.

## License scope

The MIT license in this repository applies only to the original static viewer code and written materials in this repository. It does not grant rights to the BadmintonAutoCut internal project, any source video or annotation, third-party code or model, or any other project asset. This repository includes no third-party assets or dependencies.
