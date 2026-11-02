# BRV-0026 Movement setup contract review — 2026-10-06

## Scope and proposal state

Read-only review of the Training API proposal
`docs/superpowers/specs/2026-10-06-authoring-assets-contract-amendment.md` at
Training worktree HEAD `974981ddf415c1c4c3397762531c1cd71ac63bd5` (proposal base stated
inside the document: `da4eb8fa47382c25d9242e36772bcb5bacde61fd`). The Training worktree was
clean: no diff, no implementation files changed.

This review reconciles section 3's proposed `MovementSetupRefV1`/producer manifest with the
actual Movement Studio workspace and catalog semantics in the owned Movement checkout. The review maps directly to proposal section 3 lines 295-370 (setup ref, manifest, operations, architecture decision) and its Tactics delta lines 371-389. It
also checks the section 1/3 producer, broker, credential and hosted-player boundaries. It does
not implement a schema, API, Studio, player, provisioning, deployment, rebake or contract
change.

## Finding

Section 3 is directionally compatible with the current package, but the first independent
Movement setup must be narrower than the whole Studio workspace. The actual Studio is a
browser-local editor over one immutable revision-8 asset:

- `athlete/viewer/src/catalog.js:16-27` builds one model (`netball-athlete`), two choices
  (`skirt`, `shorts`) and the loaded GLB/library's 17 clips. The kit choice is a runtime
  visibility/material variant over the same GLB: the package roles are `Kit_Jersey`,
  `Kit_Shorts` and `Kit_Skirt`.
- `athlete/viewer/src/workspace.js:6-34` validates a setup against the exact `assetHash`,
  clip id and time, kit id, height `1.60..1.95`, speed `.25..2`, gait, optional Tactics
  preview scenario, three hex colours, camera vectors and an exact per-bone pose. It also
  stores local playback/debug flags (`loop`, `carry`, `skeleton`, `wireframe`).
- `athlete/viewer/src/main.js:148-169` makes the distinction that matters for the contract:
  `driver: clips` samples the native GLB action, while `driver: tactics` uses the Tactics
  pose engine and a local demo project. `scenario: receive-pivot` is likewise a local
  Tactics footwork demonstration, not a Movement-owned clip or package resource.
- `athlete/viewer/src/main.js:235-299` loads the static manifest, movement library and GLB,
  builds the Tactics adapter and exposes local capture/restore. There is no setup id/version,
  server catalogue, return session, immutable publication or hosted Movement player.

The current candidate is concrete package evidence, not a service contract:

- model revision `8`, `modelId` `netball-athlete`
- GLB `netball-athlete.glb`: 17,090,940 bytes,
  SHA-256 `55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412`
- movement library `movement-library.json`: 54,644 bytes,
  SHA-256 `b807503ad5c7e58217ab1fb988f72be5c181360689dd811928ea7abdab4fac51`
- package manifest `manifest.json`: revision 8, 17 clips, 70 joints and 21 Tactics-required
  joints; it also records `movementSourceCommit` and garment roles.
- `movement-library.json` carries per-clip duration, phases, ball dynamics, source-check
  state and coach-approval state. Coach approval is false for this candidate and must not be
  inferred from publication availability.

The package manifest is not ready to publish verbatim: its `sources[].path` values are
machine-local absolute paths. A producer runtime manifest must be sanitized to relative
runtime dependencies and retain only the exact hashes/bytes needed by the player.

## Setup fields: supported, conditional and unsupported

| Studio field | Contract disposition | Evidence / reason |
|---|---|---|
| `modelId`, revision, GLB `assetHash` | Supported and required | Exact identity exists in the candidate manifest and is checked by `validateSetup`. |
| `kit: skirt \| shorts` | Supported | Both are catalogued and backed by named GLB garment roles. |
| kit colours (`primary`, `accent`, `shorts`) | Conditional | The player can set the three hex materials; publish only if colour is part of the immutable setup, otherwise normalize to an explicit default. |
| `clip`, `time` and clip duration | Supported for `driver: clips` | All 17 ids/durations are loaded from the actual GLB/library; time is bounded by the selected clip. |
| `speed`, `loop` | Playback settings only | Studio supports `.25..2` and loop; they do not change the authored clip or asset identity. Map them to the declared playback policy only if the Movement player owns that rule. |
| `height` | Conditional playback setting | Studio scales the rig at runtime. Preserve only with an agreed player scaling rule and unit; otherwise use the player default and do not silently change proportions. |
| `pose` | Conditional, rig-bound | Exact joint transforms round-trip locally, but only against a matching rig/model hash. The API cannot validate anatomy; a producer must reject incompatible poses rather than strip them. |
| `camera.position/target` | Conditional | These are Three.js local camera vectors. They are portable only after a Movement player camera convention is defined. |
| `driver: clips` | Supported first MVP | Native Movement clip playback is the independent Movement boundary. |
| `driver: tactics`, `scenario: receive-pivot` | Unsupported in an independent Movement setup | They call Tactics' pose/footwork engine and a local demo project. They belong behind a Tactics presentation reference, not a Movement setup manifest. |
| `carry` | Conditional and local-only today | Studio's private carry-ball IK presentation is not the Tactics match-ball timeline and has no standalone Movement publication semantics. |
| `skeleton`, `wireframe` | Unsupported for production publication | Debug/review toggles; keep them out of the immutable setup or explicitly mark them review-only. |
| browser `saved`, `drafts`, notes, workspace key | Unsupported | Browser-local review state, not team identity, immutable asset identity or server persistence. |

## Smallest source-backed manifest example

This is the smallest producer-owned shape that can be filled from the current package for a
stationary/native Movement clip. The ids beginning `setup_`/`mver_` are server-issued
placeholders in this example; they are not present in today's package. `poster` and the
player-access envelope are intentionally called out below because the current Studio does
not generate them.

```json
{
  "kind": "braven-movement-setup-manifest",
  "schemaVersion": 1,
  "setupId": "setup_netball-athlete",
  "setupVersionId": "mver_server_issued",
  "model": {
    "modelId": "netball-athlete",
    "revision": 8,
    "assetSha256": "55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412"
  },
  "kit": {
    "id": "skirt",
    "colours": { "primary": "#087e76", "accent": "#ef775e", "shorts": "#202b31" }
  },
  "animation": {
    "clipId": "netball_chest_pass",
    "timeSeconds": 0.7,
    "durationSeconds": 1.5833333730697632,
    "speed": 1,
    "loop": false
  },
  "assets": [
    {
      "path": "netball-athlete.glb",
      "contentType": "model/gltf-binary",
      "bytes": 17090940,
      "sha256": "55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412"
    },
    {
      "path": "movement-library.json",
      "contentType": "application/json",
      "bytes": 54644,
      "sha256": "b807503ad5c7e58217ab1fb988f72be5c181360689dd811928ea7abdab4fac51"
    }
  ]
}
```

This is a source-backed candidate payload, not an approved wire schema. Before an API can
mark it available, the producer still needs to add and inventory a generated poster/still,
define the stable hosted Movement player and its camera/height/pose compatibility rules,
and publish a short-lived access resource that signs only these exact generations. The
current `manifest.json` should be sanitized rather than uploaded as a runtime dependency
because of its local source paths.

A setup carrying a Tactics-driven moving receive/pass, ball trajectory or Tactics project
must not be made by adding `driver: tactics` to this payload. It should be a Tactics
presentation reference (the independent Tactics gate), with the Movement package used by
that player only where the existing Tactics integration contract says so.

## Broker, organisation binding and credential boundary

The proposal has the right security direction and should retain these invariants:

- Human session creation takes organisation/tenant from authenticated identity, never from
  `context` or a client-supplied organisation id. `returnUrl` is allowlisted; no token or
  signed asset URL is placed in the redirect.
- The Movement Studio may receive an opaque authoring URL/session id and use human
  `movement:author`/`movement:reference` permissions. An opaque session id is not an
  organisation proof by itself.
- The producer worker resolving the session must authenticate as the Movement producer,
  verify that the session's initiating human and the selected setup belong to the same
  organisation, verify the exact setup version is `available`, and submit only
  `{setupId, setupVersionId}` (or the explicitly approved equivalent). The worker owns
  `movement:publish` and `movement:session:resolve`; neither credential can enter browser
  JavaScript, local storage, a redirect URL or item JSON.
- The proposed human `GET /movement/authoring-sessions/{id}` is sufficient for a browser
  owner to observe its own state, but the producer-side broker still needs a trusted way to
  bind the initiating human/org when resolving. Reuse the bounded context principle from
  the Tactics producer review (a producer-authenticated context read or an equivalent
  server-side broker assertion) rather than trusting browser context or return parameters.
  Reserve that auth/contract decision before implementation; this review does not add a new
  route or namespace.
- `POST /movement/setup-versions/{id}:access` should issue no-store, generation-bound
  signed resources with the proposal's short expiry (<=300s). URLs are fetched by the
  player, never persisted in setup refs, item values, release records or audit data.

## Practical hosted producer/player delta

The smallest implementation slice after API/auth reservation is:

1. Add a Movement Studio launch/return adapter that accepts the opaque authoring session,
   lets a human select only the supported native setup fields above, and preserves the
   allowlisted return target.
2. Add a producer service that serializes the selected native clip setup, sanitizes the
   runtime inventory, renders a poster, allocates an immutable setup version, uploads exact
   GLB/library/poster bytes, finalises, and polls `available`/`rejected`.
3. Resolve the session server-to-server with the exact immutable setup identity. Training
   reads the authoritative result, saves the ref into its normal item revision, hard-reloads
   it, and previews through the Movement access resource.
4. Host one stable, read-only Movement player that consumes the setup manifest, verifies all
   manifest dependencies by hash, supports the declared kit/clip/time/playback policy and
   renders the poster fallback. It must not depend on browser-local workspace state or on a
   Tactics checkout.
5. Keep Tactics-driven moving play as the separate Tactics journey and acceptance gate.
   Do not make Training's Movement ref carry a Tactics scenario, local `receive-pivot` demo,
   or raw GLB URL.

Current evidence satisfies only the static package/model/kit/clip half of this delta. No
hosted Movement Studio/player or Movement server handoff was proven in this review, so the
independent Movement create/select/return/embed/save/reload/preview gate remains open.

## Exact review state

- Training proposal worktree: `F:\Repositories\braven-training\.worktrees\api-brv0026-contract-definition`
- Proposal HEAD: `974981ddf415c1c4c3397762531c1cd71ac63bd5`
- Proposal worktree diff: clean (`git diff --stat` empty)
- Movement source used for reconciliation: `F:\Repositories\braven-movement-netball-athlete`
- No code, API contract, deployment, package or Blender files changed by this review.


