# Movement/Tactics readiness receipt

Date: 2026-10-06 (Africa/Johannesburg)

Status: **Worker Review — local athlete playback ready; Training roundtrip not ready**

This is a read-only readiness inspection. No source code, model, export, merge,
deployment, rebake or dependency installation was performed. The only new file is
this receipt.

## Exact source state

| Area | Worktree | Branch | HEAD | Dirty/state |
| --- | --- | --- | --- | --- |
| Movement | `F:\Repositories\braven-movement-netball-athlete` | `codex/netball-athlete` | `037880badbf72720ab715b40101d80e5a6c8930e` | clean at inspection; local branch is 9 commits behind `origin/codex/netball-athlete` (`5c7f33b020d3866caddaab1479bdbf0d8a5967a4`) |
| Tactics | `F:\Repositories\braven-tactics-netball-athlete` | `codex/netball-athlete` | `a1f6c2dad58b3c247b28a908066dad7ac88268b4` | clean; tracks the same remote branch |

The Movement worktree is intentionally not being fast-forwarded in this inspection.
After this receipt was written it has one untracked receipt file; no implementation
files were changed.

## GitHub delivery state

- Movement PR [#133](https://github.com/braven-pvm/braven-movement/pull/133) is **open**, base `main` at `c4652ec492d2c0eb265b1a457d610d60c5a02fe7`, remote head `5c7f33b020d3866caddaab1479bdbf0d8a5967a4`. Both reported `python` checks passed. `merged_at` is null; the API's `merge_commit_sha` `b9b830608a4ff87c5898ba0d5a62bebaa4c1a23c` is therefore not treated as a completed merge.
- Tactics PR [#501](https://github.com/braven-pvm/braven-tactics/pull/501) is **merged** at `0c9e5161a07bab2bda6749bc2f4910693a6eafdb`; its recorded check passed. Current remote Tactics `main` is `4b80c99fdad17d4d40e3dcfcede20bcc87228dfb`, 23 commits ahead and 0 behind that merge.

## Immutable athlete package

Source package: `E:\cloud services\OneDrive - About IT Group (Pty) Ltd\Documents\ChatGPT\Braven Movement\Netball Athlete\candidates\08-jog`

- Manifest revision: `8`; generator: Independent Blender/MPFB authoring; source commit `b4f707478ddea3240110f80b5d8e7373a884cb90`.
- Runtime GLB: 17,090,940 bytes, SHA-256 `55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412`.
- Editable Blender master: 57,041,412 bytes, SHA-256 `dec26600abc7089e1f9f6ca301a2882f690bdedffe9fbbb254ef7dc6effddbb7`.
- The package has 70 deformation controls, 74,347 vertices, separate `Kit_Jersey`, `Kit_Shorts` and `Kit_Skirt`, and 17 finite clips: Defence, Jog, Jump_reach, 12 imported netball techniques, Ready and Receive_pass.
- Native verification records Blender reopen/IK/GLB roundtrip and garment seam checks. Jog scope verification says only `Jog` changed; all other 16 actions and mesh attributes remained unchanged.
- The Tactics package receipt pins the same GLB hash and revision 8. It records seven source checks passed, five techniques needing review, and `coachApproved: false`. Runtime sole binding is a cloned per-rig correction; the native GLB weights were not rebaked.

## Runtime evidence

### Local Movement and Tactics

The following servers are running and returned HTTP 200:

- Movement Studio dev: `http://127.0.0.1:5391/` (Vite PID 52656).
- Tactics athlete dev: `http://127.0.0.1:5395/` (Vite PID 54772).
- Movement compiled preview: `http://127.0.0.1:5397/` (Vite preview PID 53980).

The Movement Studio browser surface loaded the actual model, showed 17 animations,
editable kit controls, a controlled ball and the 70-control rig. The Tactics surface
loaded a normal netball play and exposed the Braven Movement panel with full-body
animations, the selected chest-pass clip, source-check state and the automatic
throw/receiver wording. This proves local athlete playback and Tactics-side motion
selection. It does **not** prove a Training create/select/return/embed/save/reload
roundtrip.

### Hosted specialist availability

- `https://tactics.bravenperformance.co.za/` returned 200 with build marker
  `muntizzx 4b80c99`.
- `https://tactics.bravenperformance.co.za/figures/braven-athlete/athlete.glb`
  returned 200 and its downloaded bytes match the immutable local GLB exactly:
  17,090,940 bytes and SHA-256 `55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412`.
- Hosted `figures/clips.json` returned 200 and contains 12 root clips, including
  generic jog/run plus seven imported netball entries. It is not a complete mirror of
  the 17-clip Movement catalog and no hosted Movement Studio URL was established.
- The published Movement API development service is live: `/health/live` and
  `/health/ready` both returned 200; ready checks reported PostgreSQL and Tactics
  assets as `ok`.

## Existing Training contract versus missing application integration

The Training platform already contains the publication/session primitives:

- Publication lifecycle: allocate, manifest register, upload, finalise, verify, then
  `available` or `rejected`, with SHA-256 inventory and immutable object paths.
- Catalogue/detail/presentation routes: `GET /tactics/diagrams`,
  `GET /tactics/diagrams/{diagramId}/versions`,
  `GET /tactics/diagram-versions/{diagramVersionId}` and
  `GET /tactics/diagram-versions/{diagramVersionId}/presentations`.
- Authoring handoff routes: `POST /tactics/authoring-sessions`,
  `GET /tactics/authoring-sessions/{id}` and
  `POST /tactics/authoring-sessions/{id}:resolve`.
- The generated contract pins `diagramId`, `diagramVersionId` and `presentationId` in
  `TacticsPresentationRefV1`; it separately defines a draft reference, playback policy,
  poster/still, manifest URL, asset base URL, manifest hash and expiry.

The missing part is the Training authoring and reader path:

1. `platform/sdk/typescript/src/movement-api-client.ts` currently wraps only
   `listTacticsPresentations` for Tactics; it has no high-level create/get/resolve
   authoring-session, diagram discovery or version-list methods.
2. `apps/authoring_web/src/api/AuthoringApi` and
   `createMovementAuthoringApi` expose no Tactics session/reference operations.
3. `GuidedStepsEditor` still offers only `none`, `drillDiagram`, `specificDiagram` and
   `media`; diagram choices are represented as legacy frame metadata. Unknown
   `tacticsSequence` values are preserved as opaque data, but are not editable or
   resolved.
4. `AuthoringPreview` renders a placeholder stating that the Tactics presentation
   target will render there. It does not load a manifest, model, ball or read-only
   playback resource. Save/reload therefore has no verified immutable Tactics ref.

The minimum missing contract is therefore an application-level binding from a Training
item field/step to `TacticsPresentationRefV1` (or `TacticsDraftRefV1` while editing),
plus the authenticated session and playback calls. A GLB URL alone is insufficient:
Training needs the immutable diagram/version/presentation identity, still fallback,
manifest and asset URLs, expiry, playback policy, availability/rejection semantics and
release validation.

The approved roadmap has a second, independent gate that remains open: a real Movement
create/select/return/embed/save/reload/preview handoff for the athlete model, kit and
selected clip. The static `/athlete-assets/*` bundle and Tactics import script are
producer evidence only; they do not provide that Training handoff. The Movement-side
asset identity, authenticated return/session semantics and consumer playback location
still require a producer/API definition and implementation. This receipt does not waive
that gate or invent its namespace.

## Next acceptance envelope

The next implementation is ready for review only when both the Tactics and Movement
journeys pass in a real authenticated Training browser session. The Tactics half is:

1. Open a drill item and choose **Create Tactics presentation** or **Select existing**.
2. Training sends `POST /tactics/authoring-sessions` with intent, item/step context,
   an allowlisted return URL and an idempotency key; it launches the returned Tactics
   authoring URL.
3. Tactics creates or selects a presentation and resolves the session with
   `diagramId`, `diagramVersion` and `presentationId`, using `If-Match` and an
   idempotency key.
4. Training obtains the server-side session result, writes the immutable reference into
   the item revision, saves with the normal ETag/idempotency path, reloads the item from
   the API and shows the same three IDs.
5. Training preview resolves the playback resource, renders the read-only Tactics
   player with the declared still/poster fallback and controls policy, and shows the
   actual court, athlete kit, animation and authoritative ball.
6. A cancelled, expired, rejected or superseded session/version remains visible as a
   recoverable authoring error; a draft reference renders in preview but is rejected by
   release validation. The browser receipt must include save, hard reload, preview and
   release-validation evidence.

The independent Movement half must show the same lifecycle for a model/kit/clip asset:
Training creates or selects through the approved Movement handoff, receives an immutable
asset identity and ready/not-ready/cancel outcome, embeds the declared consumer runtime,
saves the reference into the item revision, hard-reloads it from the API, and previews
the actual athlete/kit/clip. A static GLB fetch or local browser storage does not satisfy
this gate.

Until this envelope is witnessed, status remains Worker Review. Local Movement/Tactics
playback and the hosted GLB are useful evidence, but they are not Training integration
evidence.

## Verification ledger

- Passed/observed in this pass: exact worktree/PR inventory; immutable GLB hash; hosted
  GLB hash; local Movement/Tactics HTTP and browser loading; hosted Tactics/API health.
- Recorded prior evidence: source/garment/IK checks; jog and moving-catch RED-to-GREEN
  regressions; Tactics suites and browser receipts in `JOG-CONTACT-SYNC.md`,
  `GAIT-DEEP-DIVE.md`, `JOG-REPAIR.md` and `MOVING-CATCH-REPAIR.md`.
- Skipped/not checked in this pass: full Movement/Tactics test rerun; Blender rerun;
  authenticated Training browser roundtrip; Training dependency install or server
  start; coach approval for five imported techniques.
