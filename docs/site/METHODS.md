# Methods and evaluation scope

[Rendered English methods page](methods.html) · [研究方法中文版](zh/methods.html) · [Bilingual research portfolio](./)

This gallery shows historical model outputs and research figures. It does not certify an automatic editor or change the production pipeline.

## Oct 3, four-source visual study

The source IDs are `26100301`, `26100302`, `26100303`, and `26100304`, all recorded on 2026-10-03. The per-frame research renderer is `M6_POSE_MOTION_PLUS_TRACKNET`: Pose detector slots, TrackNet V3 raw candidates, InpaintNet output where available, and an offline noncausal state estimate. Sources 26100302–04 use frozen zero-shot parameters without target-GT tuning. Source 26100301 is in-sample and is not used as a headline success.

The four-source raw scatter comes from the original candidate CSV and retains its image-space x/y points and confidence. It includes points inside existing editorial LIVE intervals. Each point remains unassociated: no track, flight path, interpolation, or CurrentCourt admission is implied. The report heatmap is a separate aggregation into spatial cells and loses point-level timing.

Near/Far are experimental image-y pose slots. They are not stable player identities or Court-side labels. Missing slots remain missing, and UNKNOWN remains visible. No physical Hit truth or reliable player attribution is inferred from Kwyoke candidates.

## Editorial timelines and boundary candidates

GT is the human-edited editorial interval timeline. It measures editing relevance, not physical shuttle-in-play truth. The full-source categorical figure uses separate GT and M6 A rows. Its generator assigns LIVE green (`#14916d`), DEAD slate (`#556174`), and UNKNOWN amber (`#e3a12f`). The tail-safe probability figure is a different analysis arm; it shows P(LIVE), report thresholds, editorial intervals/UNKNOWN margins, and quarantined tail regions. Do not read the two plots as one model run.

START/END screenshots show frozen M6 boundary candidates. Their event times are retained separately from the nearest sampled frame PTS. A candidate is not a formal Rally boundary. The report evaluates boundary matching one-to-one against editorial intervals at ±0.5 seconds; it does not establish physical start/end events.

## Tail-safe report metrics

The 2026-10-12 offline study compares four sources from one date. `PLAYER_TRACKNET_CONTEXT_TAIL_SAFE` is the tail-safe arm. The unguarded `PLAYER_TRACKNET_CONTEXT` arm is a separate comparator.

| Offline arm | Balanced accuracy | UNKNOWN | START | END | Complete boundary pairs matched | Precision | Recall | Editorial LIVE lost | Editorial DEAD kept |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `PLAYER_TRACKNET_CONTEXT_TAIL_SAFE` | 87.75% | 5.08% | 139/148 | 93/148 | 79/148 | 59.85% | 53.38% | 164.33 s | 62.85 s |
| Unguarded `PLAYER_TRACKNET_CONTEXT` | 87.44% | 5.46% | 138/148 | 100/148 | 82/148 | 61.65% | 55.41% | 175.60 s | 51.12 s |

The table values are editorial interval/state metrics from this four-source, one-date offline experiment. `79/148` and `82/148` are different arms. Neither is a count of production Rally exports.

## Separate archived ablation and Court evidence

The 2026-10-13 ablation image traces to an archived same-protocol table and reports change in complete Rally boundary-pair counts for four sources from one date. It is not the tail-safe table above, and its count delta should not be interpreted as the same metric as boundary recall or precision.

The `260807-92` image and CurrentCourt-admitted spatial count map belong to a separate 2026-08-07 Court-scoped study. The Court checkpoint shows a PASS at the recorded START/MIDPOINT checkpoints with source-bound visual registration. The spatial plot is an image-pixel count map, not a Court-plane projection or physical-speed estimate. Neither figure belongs to the Oct 3 cohort.

## Production boundary and limitations

The public screenshots are offline research renderings. They do not run the production EventFirst pipeline. EventFirst remains the implemented production path with status `PRODUCTION_NOT_READY`; no formal Rally, KeepTimeline, or export acceptance is claimed. The showcased research study records zero accepted production Rally/Keep/export results. See the [original research report](RESEARCH_REPORT.html) and [reproducibility notes](REPRODUCIBILITY.md) for provenance and scope.
