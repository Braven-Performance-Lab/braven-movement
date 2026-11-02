# BRV-0026 latest frozen reconciliation — 2026-10-06

## Exact review state

Reviewed the frozen Training definition at commit
`0cb759124400c6bf144bc7e232ef9661093194a` in
`F:\Repositories\braven-training\.worktrees\api-brv0026-contract-definition`.
The commit is `docs(api): simplify exact-command approval and freeze safe cutover gates`.
No product, API, Studio, player, credential, deployment, asset or Blender files were changed
by this review.

Movement source reconciled at exact HEAD `037880badbf72720ab715b40101d80e5a6c8930e`
(`codex/netball-athlete`) and candidate `08-jog` package. The Movement tree contains only
review receipts as untracked files.

## Bounded result

**PASS with concrete FIXUPS.** The latest amendment is a material improvement over the
previous bearer-confirmation proposal and is compatible with the two specialist products.
It now stores the exact owner command server-side, returns a nonsecret `approvalId`, keeps
resolution service-only, and closes every unsafe legacy read/create-replay/context/approval/
resolve/replay path before mixed-version cutover or rollback. No weaker service-only resolve
or guessed owner migration is acceptable.

The remaining blockers are evidence/implementation gates, not a need for a new contract:

1. The actual package has 17 GLB clips but only 12 `movement-library.json` technique entries.
2. The existing Studio validator accepts native clip time up to `clip.duration + 0.01`, while
   the frozen publication policy requires strict `[0,duration]` with no silent clamp.
3. Canonical per-clip camera fixtures and the hosted player/poster/access path do not exist.
4. The real Training/Tactics/Movement authenticated create/select/return/save/reload/preview
   journey is not implemented or witnessed.

## Approval and cutover reconciliation

The narrowed protocol is the smallest sufficient secure boundary under the frozen threat
model:

- **Create:** server derives and stores `initiatingPrincipalId`, organisation, product,
  configured producer principal/audience and canonical request hash. Replay identity is
  `(organisation, initiator, product, idempotency key)`; same owner/body replays, same-org B
  creates a distinct session, and changed body conflicts.
- **Context/bootstrap:** one producer-authenticated bounded context read or equivalent
  server-side launch broker proves configured service/audience, owner/org membership and
  pending/unexpired state. It cannot become an alternate resolver or a browser-facing second
  workflow.
- **Approval:** after the exact resource is available, the authenticated initiating owner
  approves the closed canonical command. The response is only `{approvalId, expiresAt}`;
  possession grants nothing. The approval stores the exact command/digest, owner/org,
  producer/audience binding, session version, expiry and receipt. No bearer token, token hash,
  encryption key, or approval-read/revoke endpoint is required by the evidence.
- **Resolve:** the configured producer submits the exact existing terminal command, approval ID,
  idempotency key and `If-Match`. One transaction rechecks current auth/grants, trusted
  runtime audience, product/org/session/owner, approval command/version/expiry, readiness and
  session CAS before consuming approval and writing the terminal receipt.

The amendment correctly keeps service credentials out of browser code, redirects, item JSON,
local storage and audit data. Original authorized service/key/body replay returns the recorded
result before stale ETag or consumed/expired approval checks; changed command/approval/session/
key cannot borrow that replay. The legacy migration requirement is strong enough only if an
actual ingress/routing gate or retired old binary prevents old handlers and internal producer
entries from serving unsafe paths; a feature flag ignored by an old binary is insufficient.

No unnecessary extra handshake should be added. Keep context and approval as bounded state
operations (or collapse context into an authenticated launch broker), but retain exact owner
approval because a separate producer service cannot prove human approval by service identity
alone.

## Native Movement profile reconciliation

The frozen first profile is source-compatible when treated as a publication snapshot, not the
whole browser workspace:

- `driver` exactly `clips`; reject `tactics`, gait demo, `receive-pivot`, carry-ball IK,
  skeleton, wireframe and browser saved/draft/note/workspace state.
- Pin `modelId: netball-athlete`, revision `8`, GLB SHA-256
  `55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412`, and
  `movement-library.json` SHA-256
  `b807503ad5c7e58217ab1fb988f72be5c181360689dd811928ea7abdab4fac51`.
  The source package `manifest.json` is 7,013 bytes with SHA-256
  `af8074bb0079ad7f5be9dc99b28dbc19bb071ef7bede3c4764e6da895e68d8aa`, but its machine-local
  `sources[].path` values must be sanitized before runtime publication.
- Pin kit `skirt` or `shorts` and all three hex colours (`primary`, `accent`, `shorts`),
  normalising only case. Do not silently default or strip a non-default colour.
- Pin clip ID, GLB/library duration agreement and `timeSeconds`; speed is `[0.25,2]` and
  loop is a boolean. Speed and loop live once in the Movement manifest. Movement references
  carry only autoplay and controls; they do not duplicate speed or loop.
- First profile requires `heightMetres: 1.75`, `pose: null`, and the producer-owned default
  camera fixture for the pinned clip/package. Non-default height, custom camera or non-null
  pose rejects with an explicit unsupported-setting diagnostic until a later versioned player
  proves the capability. The local workspace remains intact for review.

### Native camera fixture proposal for the next Models lane slice

The source `athlete/viewer/src/main.js:57-67,111-112` has three deterministic camera groups;
this is a fixture proposal, not a hosted-player proof:

| Clip IDs | position | target | Source rule |
|---|---:|---:|---|
| `Defence`, `Jog`, `Ready`, `Receive_pass`, `netball_chest_pass`, `netball_deflect_high`, `netball_double_foot_landing`, `netball_hooks_jump_pull_in`, `netball_hooks_outside_hand`, `netball_one_hand_high_pass`, `netball_one_hand_snatch_to_other_hand`, `netball_overhead_pass`, `netball_two_hand_catch_chest`, `netball_two_hand_snatch_pull_in`, `netball_two_hand_snatch_straight_back` | `[2.2, 1.8, 3.55]` | `[0, 0.93, 0]` | `view('quarter')` generic framing |
| `Jump_reach` | `[2.596, 1.9224, 4.189]` | `[0, 1.12, 0]` | quarter camera `[2.2,1.8,3.55]`, target y `1.12`, then offset `1.18` |
| `netball_bounce_pass` | `[5, 2.5, 6]` | `[0, 0.8, 1.3]` | explicit bounce-pass quarter framing |

These values are derived from the current source and should be frozen by Models with the
actual floating-point representation/projection fixture before availability. They do not
claim one universal camera: the current app has user orbit and manual camera state, and the
special clips deliberately reframe. A publication snapshot must use the producer default,
not inherit a browser camera.

## Concrete native blockers

### 1. Clip/library coverage must be resolved

The current candidate `manifest.json` lists 17 animations, while `movement-library.json`
contains 12 techniques. The five manifest clips without a library technique are:

`Defence`, `Jog`, `Jump_reach`, `Ready`, `Receive_pass`.

The frozen policy says the producer verifies GLB/library agreement, but these five have no
technique record to agree against. Before implementation, Models/API must choose one of:

- restrict first publication profile to the 12 clips present in `movement-library.json`; or
- make the package `manifest.json` animation inventory authoritative for those five and
  explicitly mark movement-library metadata optional/absent for them.

Do not pretend five general/native clips are library-backed, generate metadata silently,
or reject them after a local UI represented them as available without an explicit diagnostic.
The narrower 12-clip route is the safer first implementation if no metadata fixture is added.

### 2. Strict publication time guard must sit above local workspace validation

`athlete/viewer/src/workspace.js:6-14` currently accepts native clip time through
`clip.duration + 0.01` to tolerate local playback edges. The frozen manifest requires strict
`0 <= timeSeconds <= duration` and no silent clamp. The publisher must therefore perform a
second strict check and reject an out-of-range saved setup, preserving the original local
workspace. It must not claim every Studio-valid saved setup is publishable.

### 3. Hosted player/access evidence remains absent

The candidate has no setup/version IDs, poster, hosted Movement player, or Movement server
handoff. The producer still needs relative path/MIME/bytes/SHA-256/generation inventory,
poster generation, exact dependency access, no-store short-lived resources, hash verification
for every dependency and a stable read-only player. The independent Movement gate remains
open; the hosted Tactics GLB cannot satisfy it.

## Remaining decision and acceptance envelope

- Decide whether native setup v1 is 12 technique clips only or all 17 with an explicit
  manifest-authoritative general-clip branch.
- Models must freeze the per-clip camera fixture and player acceptance before publishing any
  setup; until then non-default camera/height/pose rejects.
- Prove both products' owner-bound approval/replay/expiry/legacy cutover with real PostgreSQL
  transactions and current authenticated producer/runtime audience; no definition text or
  focused probe is auth GREEN.
- Witness Training create/select, producer publication, exact owner approval, server resolve,
  return, item save, hard reload and read-only playback for Tactics and Movement separately.

## Ledger

- **PASS:** latest frozen SHA reviewed; nonsecret approval simplification; exact canonical
  command validation; one Movement speed/loop owner; strict default restrictions; owner/org/
  product/resolver/audience, expiry/CAS/replay and legacy-route closure are explicit; native
  hashes/kit/clip/time policy reconciles with current source.
- **FIXUPS:** five clip/library coverage decision; strict time guard above local validator;
  camera fixture/player/poster/access proof; full authenticated journeys and PG/concurrency
  cutover tests; Tactics producer adapter.
- **Not checked:** service credentials, database migrations, hosted player, cloud writes,
  deployment, Blender or asset rebake.

No product/API/source files were modified by this review.

## Publication quota and immutable path follow-up (2026-10-06)

This is a bounded proposal for the next Models/API definition review, not a tested
storage or player capability. It reconciles the frozen Training definition at the full
SHA `0cb759124400c6bf144bc7e232ef9661093194a4` with Movement source HEAD
`037880badbf72720ab715b40101d80e5a6c8930e` and the approved `08-jog` candidate.

### Measured package evidence

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `manifest.json` | 7,013 | `af8074bb0079ad7f5be9dc99b28dbc19bb071ef7bede3c4764e6da895e68d8aa` |
| `netball-athlete.glb` | 17,090,940 | `55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412` |
| `movement-library.json` | 54,644 | `b807503ad5c7e58217ab1fb988f72be5c181360689dd811928ea7abdab4fac51` |

The measured setup manifest plus model/library payload is 17,152,597 bytes. No poster,
setup ID/version, or hosted read-only player exists in this candidate. The current local
compiled viewer baseline is `index.html` 11,252 bytes, hashed JS 833,966 bytes, CSS
16,619 bytes and `studio-build.json` 561 bytes, 862,398 bytes total. Source `.blend`
files and verification material are excluded from a publication package.

### Conservative v1 limits

- `manifest.json` is UTF-8 JSON, maximum **131,072 bytes (128 KiB)**. The measured
  manifest is 7,013 bytes. This is the setup document and is counted in the package total.
- The publication inventory is exactly one manifest, two required payload resources
  (`runtime/netball-athlete.glb` and `runtime/movement-library.json`) and one required
  still (`runtime/poster.webp`): **3 runtime entries / 4 files including the manifest**.
  `resources[]` therefore has a maximum of 2 entries and `still` is exactly 1 for v1;
  there are no unbounded auxiliary files.
- Every inventoried runtime file is at most **18,874,368 bytes (18 MiB)**. The poster
  has a tighter **524,288 byte (512 KiB)** cap. The current GLB is 17,090,940 bytes and
  therefore fits with a bounded margin; the library is 54,644 bytes.
- The complete setup package (manifest, model, library and poster) is at most
  **20,971,520 bytes (20 MiB)**. With the measured files and a poster at its cap, the
  package would be 17,676,885 bytes, leaving 3,294,635 bytes. Any extra file, oversized
  manifest or over-budget poster rejects before signing.
- The read-only player is a fixed, producer-owned static bundle, separately capped at
  **2,097,152 bytes (2 MiB)** and at most four files: `player/index.html`, one hashed
  `player/assets/index-<contenthash>.js`, one hashed CSS file and the small
  `player/studio-build.json` build receipt. The current 862,398-byte compiled baseline
  fits. No source maps, `.blend` files, arbitrary HTML/JS uploads or external runtime
  dependencies are admitted. This player allowance is not added to the 20 MiB setup
  package quota.

### Exact paths and generation rules

Store each immutable version below a setup-version root:

```text
movement/setups/{setupId}/versions/{setupVersionId}/manifest.json
movement/setups/{setupId}/versions/{setupVersionId}/runtime/netball-athlete.glb
movement/setups/{setupId}/versions/{setupVersionId}/runtime/movement-library.json
movement/setups/{setupId}/versions/{setupVersionId}/runtime/poster.webp
```

The manifest inventories only these normalized relative paths (forward slashes, no `..`,
no absolute source paths), MIME, byte length, SHA-256 and immutable storage generation.
The GLB and library are byte-for-byte copies of the measured candidate. The poster is a
producer-generated 512x512 WebP (maximum 512 KiB) rendered from the pinned GLB and the
frozen per-clip default camera; its generation, bytes and hash are recorded before the
setup can become available. The six machine-local `manifest.sources[].path` values are
provenance only and never enter runtime metadata.

Access signs only these exact inventoried generations, is `no-store`, and expires within
300 seconds. A stable read-only player may request only the versioned manifest, the two
runtime payloads and the still through that access result; it may not enumerate sibling
paths or mutate setup state. These numeric limits and paths are proposed evidence, not
capability-tested storage/player support.
