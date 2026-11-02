# BRV-0026 frozen definition review — 2026-10-06

## Review state

Reviewed the frozen Training API amendment at commit
`593101969a43b7a45353bff4027494474632999a`:

- Worktree: `F:\Repositories\braven-training\.worktrees\api-brv0026-contract-definition`
- Branch: `codex/training-api/brv-0026-asset-contract-definition`
- Worktree HEAD when inspected: `52c5a6a5066a5314d59c36be2f9c069bf8a8dd78`
- Frozen amendment SHA reviewed directly: `593101969a43b7a45353bff4027494474632999a`
- Proposal section 1 owner/confirmation additions: lines 205-339
- Native Movement policy and boundary: lines 470-588
- Tactics producer delta: lines 590-619
- No source, API, Studio, player, asset, credential, deployment or Blender files were changed.

This receipt is a read-only specialist review, not architecture acceptance or implementation
permission.

## Bounded result

**PASS — definition is materially safer and source-compatible, with fixups below before
implementation assignment.** The amendment now closes the prior ownerless-session gap by
requiring durable `initiatingPrincipalId`, product/org binding, configured producer
principal/audience, owner-only status/return, exact command confirmation and atomic
expiry/CAS/replay checks for both Tactics and Movement. It also narrows the first Movement
profile to the native clip driver and gives speed/loop one owner.

The current specialist products still provide package/playback evidence only. They do not
provide the Training session, owner proof, immutable publication or hosted Movement player.
No green end-to-end gate is claimed.

## Native Movement minimum: accepted source semantics

The frozen policy matches the actual Studio/catalog when interpreted as a distinct
publication snapshot rather than a browser workspace:

- `driver` must be exactly `clips`. Reject `tactics`, the local gait demo and
  `receive-pivot`; they use the Tactics pose/footwork engine and cannot be silently
  converted into a Movement clip setup.
- Pin `modelId: netball-athlete`, revision `8`, the exact GLB SHA-256
  `55c611f1a525c1ec873dfe2aa01970f806c1090c9081973ac14ca1148847a412`, and the exact
  `movement-library.json` SHA-256
  `b807503ad5c7e58217ab1fb988f72be5c181360689dd811928ea7abdab4fac51`.
  The package manifest itself is `7,013` bytes with SHA-256
  `af8074bb0079ad7f5be9dc99b28dbc19bb071ef7bede3c4764e6da895e68d8aa`; its absolute
  `sources[].path` members must be removed from any runtime inventory.
- Pin kit `skirt` or `shorts` against the named GLB garment roles. Preserve all three
  material colours (`primary`, `accent`, `shorts`) as immutable setup state, normalising
  only hex case. No hidden default or colour stripping is safe because the Studio exposes
  these as user-controlled state.
- Pin a real clip id, its library/GLB duration agreement and finite `timeSeconds` in
  `[0,duration]`. Do not use animation indexes, latest aliases or silent clamping.
- Put `animation.speed` in `[0.25,2]` and `animation.loop` in the immutable Movement
  manifest, exactly once. The Movement reference carries only `autoplay` and `controls`;
  it must not duplicate speed or loop. A new excerpt is a new setup version.
- Height may be retained only as the explicit proposed `heightMetres` convention against
  producer reference height `1.75`; camera may be retained only under the explicit proposed
  `three-local-metres-y-up-v1` convention and bounded finite vectors. Neither convention is
  proven by a hosted player yet.
- The first profile must require `pose: null`. Saved bone overrides are rig-bound and need
  a separately accepted rig-hash/player profile; reject them rather than silently discard.
  `carry`, `skeleton`, `wireframe`, browser saved/draft/note state and workspace keys remain
  unsupported publication fields.

This gives one timing owner: the Movement manifest owns clip/time/speed/loop and the
player samples/loops that exact interval; specialist references own only autoplay/controls.
Tactics' existing playback semantics remain its own contract.

## Tactics reconciliation

The amendment's owner/confirmation model is compatible with the actual Tactics gap, with
one required implementation discipline:

- Tactics currently has local Firebase `uid` auth and its own `/v1/scenarios` store. That
  identity/session is not the Training `PlatformPrincipal.principalId` and must not be
  reused as the Training authoring-session owner without an explicit platform adapter.
- The Tactics app currently has no Training session context, catalogue/selection calls,
  publisher credential, resolve call or immutable return. Its `?embed=<scenarioId>` and
  local manifest builder are not a Training result.
- On a real flow, Training creates the owner-bound session. The producer receives only an
  opaque launch/session context, while `tactics:publish`/`movement:publish` and
  `*:session:resolve` stay server-side. The broker must compare the authoritative human
  principal/org to the durable session assertion before preparing or returning a resource.
- The producer must submit the exact existing terminal command: Tactics' numeric diagram
  version plus presentation id, or Movement's opaque setup version id. It must not submit a
  raw reference blob, a browser-supplied principal, a return URL, or an asset URL.
- Human confirmation must bind to that exact canonical command. A different resource,
  product, session, outcome or changed command must not reuse the confirmation. Expiry,
  revocation, readiness, configured producer audience, session version and current owner
  grant must be checked in the same commit boundary.

## Smallest sufficient secure boundary

The frozen design's security invariants are necessary; its surface can remain small if the
implementation treats the operations as one state machine rather than as separate client
features:

1. **Owner-bound create:** persist the server-derived initiator principal, organisation,
   product, configured producer principal/audience and canonical request hash. Creation
   replay is `(org, initiator, product, key)`; same owner/body replays, same-org B creates a
   distinct session, changed body conflicts. `returnUrl` is allowlisted and no secret is
   placed in it.
2. **Producer bootstrap/context:** one producer-authenticated context read (or equivalent
   server-side launch broker) may return only the bounded pending session context needed to
   author. It must prove configured service principal/audience, owner/org membership,
   pending/unexpired state and no-store response. Do not expose a second public context
   workflow or let context become an alternate resolver.
3. **Exact owner confirmation:** after the producer has prepared and the resource is
   available, the authenticated owner confirms the exact canonical terminal command. A
   short-lived, single-use, command-hash-bound opaque confirmation token is sufficient;
   it must not change session ETag/state and must never appear in redirects, item JSON,
   storage, logs or audit payloads.
4. **Producer resolve:** the configured producer submits the existing exact command,
   confirmation proof, idempotency key and `If-Match`. The API rechecks producer
   principal/audience, owner/org, current grant, pending/version/expiry, resource
   readiness and command hash, then atomically consumes the proof and CASes the session to
   terminal. Identical authenticated lost-response replay returns the recorded result;
   changed command, stale version, expired proof or conflicting key writes nothing.

This is the smallest boundary that preserves the amendment's threat model. The separate
`/context` and `/resolution-authorizations` names may be retained for clarity, but they
should not grow separate ownership, expiry or replay semantics. If the producer launch
already delivers bounded context through an authenticated broker, do not add another
browser-facing context route. Conversely, do not remove owner confirmation merely to
shorten the flow: service-only resolution cannot prove that the original human approved
this exact terminal command.

## Access/hash and hosted-player fixups

The frozen native policy is source-compatible, but these gates remain open:

- The producer must emit relative runtime inventory entries with path, MIME, bytes,
  SHA-256 and storage generation, including the exact GLB/library and a generated poster.
  `manifest.json` cannot be copied verbatim because it exposes local source paths.
- `POST /movement/setup-versions/{id}:access` may issue only no-store, generation-bound,
  short-lived resources. The player must fetch every manifest dependency and verify hashes;
  a signed base path alone is not proof of child GLB/library/texture access. URLs never enter
  setup refs, Training item values, release records or audit data.
- No hosted Movement Studio/player was proven in the specialist review. A stable read-only
  player must be built and verified against the exact kit/colour/clip/time/speed/loop policy,
  plus the proposed height/camera convention before those fields can be enabled.
- Tactics moving receive/pass remains the separate Tactics presentation gate. It cannot be
  satisfied by the Movement native profile or by a raw GLB URL.

## Remaining decision

DevMan/API/security/Models still need to reserve whether height and camera are enabled in
Movement setup v1. The package supports them locally, but the hosted player has not proved
uniform scaling or the `three-local-metres-y-up-v1` camera convention. The safe first
implementation is to require height/camera defaults or reject non-default values until that
player evidence exists; never silently strip them. Pose remains null in v1.

The product-level owner confirmation is also a deliberate security decision: retain it if
Training treats the producer as a separate service authority, which is the current frozen
model. A security reviewer may approve a broker-equivalent design only if it preserves the
same durable owner assertion, exact command hash, one-use proof, current-grant check and
atomic CAS/replay behavior. No weaker service-only resolve is acceptable.

## Review ledger

- **PASS:** frozen amendment SHA reviewed; native package identity/hash/kit/clip/time policy
  reconciled; speed/loop has one manifest owner; Movement ref no longer duplicates them;
  Tactics and Movement identities remain namespaced; owner/auth/expiry/replay/CAS principles
  are explicit for both products; no credential exposure is proposed.
- **FIXUPS:** no implementation or live authenticated journey; no hosted Movement player or
  poster/access proof; height/camera need player evidence or default/reject policy; pose must
  remain null; Tactics producer still needs its server/session adapter; Training/Models/API
  security must reserve the final handshake/context surface before implementation.
- **Not checked:** service credentials, PostgreSQL concurrency, real Training browser
  roundtrip, cloud writes, deployment, Blender or asset rebake.

No product or API files were modified by this review.
