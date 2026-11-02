# BRV-0026 Models/Integration review

Date: 2026-10-06. Read-only review against the BRV-0026 proposal.

## Smallest capability that exists today

Movement provides a versioned **static asset bundle**, not a service catalogue or
authoring handoff:

- Movement Studio serves `GET /athlete-assets/manifest.json`,
  `GET /athlete-assets/movement-library.json` and
  `GET /athlete-assets/netball-athlete.glb` from the configured immutable output
  directory. On the running local server these returned 200; the manifest identifies
  revision 8 and GLB SHA-256
  `55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412`.
- `athlete/viewer/src/catalog.js` turns the loaded GLB/library into a client-side
  catalogue of one model, two kits and 17 clips. `workspace.js` persists only in browser
  storage and requires the asset hash; it is not team or server persistence.
- The producer-to-consumer import boundary is the CLI
  `braven-tactics-netball-athlete/tools/import-athlete.mjs <athlete-output>`. It checks
  the manifest hash, copies the GLB/source metadata into the Tactics checkout and
  generates `src/data/athlete-motions.json`.
- Tactics then serves static runtime files (`/figures/braven-athlete/athlete.glb`,
  `/figures/braven-athlete/source.json` and the generated sidecar) and selects clips
  locally by clip ID. The running local endpoints returned 200; the sidecar reports
  revision 8, the same GLB hash and 17 clip IDs.

This is sufficient for local Movement preview and Tactics playback. It is not a
Movement asset select/return/version API: there is no Movement catalogue endpoint, no
Movement authoring-session endpoint, no server-side save/reload of a selected kit/clip,
and no return URL that hands a Movement asset reference to Training.

## Bounded gap and proposal

The approved MVP has **two separate gates** and both remain mandatory:

1. The Tactics gate uses the existing `TacticsPresentationRefV1`, which pins the
   immutable Tactics diagram, diagram version and presentation. Its playback resource
   carries the manifest URL, asset base URL, still/poster, hash, expiry and controls
   policy.
2. The Movement gate must provide a real create/select/return/embed/save/reload/preview
   handoff for the athlete model, kit and selected clip. The static bundle observed here
   is evidence for that producer slice, not a substitute for it. Training must not depend
   on the local Movement Studio routes or on a raw GLB path alone.

Movement currently has no service handoff contract to review. The producer/API owner
must define the smallest authenticated, immutable representation against the actual
bundle (at minimum the model asset identity, revision, SHA-256, selected kit/clip and
consumer playback location), plus ready/not-ready/cancel and save/reload semantics.
This note deliberately does not name a new namespace or claim that representation is
implemented.

If independent model/kit selection is later carried alongside a Tactics presentation,
the existing `extensions` slots on `TacticsPresentationRefV1` and
`TacticsDiagramVersionManifestV1` are a possible additive transport location, subject
to API approval and producer tests. The current producer does not emit such a
descriptor; this is only a bounded follow-up proposal.

## Review outcome

- **Supported now:** Tactics can reference an immutable presentation, and Movement can
  supply the model package to Tactics through the checked static import boundary.
- **Not supported now:** the required Training Movement create/select/return/embed/save/
  reload/preview path; Training directly browsing Movement models/kits; or a server-side
  Movement handoff/session.
- **Required BRV-0026 wording:** keep both the Tactics and Movement acceptance gates
  explicit. Mark the Movement catalogue/session as unavailable in this slice and assign
  its producer/API definition and implementation separately. Do not infer it from
  `/athlete-assets/*`, `/figures/*`, local browser storage or the static import script.
