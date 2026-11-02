# BRV-0026 Tactics producer roundtrip review — 2026-10-06

## Scope

This is a read-only review of the current Tactics producer (local `a1f6c2d`, branch
`codex/netball-athlete`, and hosted build `muntizzx 4b80c99`). It checks whether the actual
Tactics app consumes Training authoring-session context and publishes/resolves an available
immutable diagram/presentation. It does not change the API contract, implement a producer
flow, merge, deploy, or rebake the athlete.

## Finding

The current app does **not** perform the Training roundtrip. It has two separate capabilities:

1. **Tactics-owned scenario persistence.** `src/contract/cloud.ts:9-82` configures an optional
   `VITE_API_BASE`, creates `RemoteStore`, and `src/contract/remote.ts:340-567` implements
   the Tactics Worker verbs for `/v1/scenarios`, `/revisions`, `/placement`, save and delete.
   `src/main.tsx:47-55` recognises only `?embed=<scenarioId>`; this mounts the read-only
   `EmbedViewer` for a Tactics scenario, not a Training authoring session.
2. **A local Movement-shaped manifest builder.** `src/contract/manifest.ts:128-223` builds
   and validates a manifest from local scenario/storyboard state. It is a pure builder: no
   allocate, presigned upload, finalise, availability polling, authoring-session creation,
   session resolution, return URL, or immutable `TacticsPresentationRefV1` write is called
   from the client.

The Tactics API route table corroborates this boundary. `api/src/routes.ts:74-91` only has a
single-scenario route matcher, and `api/src/index.ts:1281-1390` handles scenario read/save/delete
and placement. There is no `/v1/tactics/authoring-sessions`, diagram listing, version listing,
allocate, upload, finalise, or session-resolve route in this repo.

The deployed site shows the same behaviour rather than a stale source-only result:

- `GET https://tactics.bravenperformance.co.za/` returned 200 and build marker
  `muntizzx 4b80c99`.
- Its served bundle `/assets/index-BhDw446h-muntizzx.js` contains `/v1/scenarios` but no
  `/v1/tactics`, `authoring-session`, `manifestUrl`, or `TacticsPresentationRef` strings.
- Probes to `https://tactics.bravenperformance.co.za/v1/tactics/authoring-sessions` and
  `https://tactics.bravenperformance.co.za/v1/scenarios` returned 404. These are only useful
  as evidence that the hosted frontend origin is not itself the Training publication API; they
  do **not** test the correct platform host, route prefix, HTTP method, or session id.
- The known platform base `https://movement-api-uecvvuzy3q-bq.a.run.app` returned 404 for
  an unauthenticated GET to `/v1/tactics/authoring-sessions`. That probe used the wrong route
  shape for the deployed contract (`/tactics/authoring-sessions`, POST to create, GET with a
  session id to read) and therefore proves nothing about platform availability. The conclusion
  rests on the Tactics source and served bundle: no browser client call exists that would make
  the session roundtrip.

The repository docs state the same current boundary, and are design/status evidence rather
than implementation: `docs/access-acceptance.md:340` calls Movement publication blocked on an
OAuth scope; `docs/persistence-plan.md:296,367,379-388` records `/v1/scenarios/{id}/publish`
as later work and says the manifest is built but allocate/upload/finalise is not implemented;
`docs/persistence.md:512-526` repeats that `tactics:publish` credentials are still absent.
`docs/movement-api-amendments.md:250-289` describes the proposed existing Training hand-off
(`POST /v1/tactics/authoring-sessions`, then server-side GET resolution) and
`:323-340` defines the author/reference/publish scope split. Those proposals are not consumed
by the current Tactics client.

## Gate result

- **Tactics author/select/return/embed/save/reload/preview:** **not met** for the Training
  authoring-session contract. Local scenario save/reload and `?embed=` playback are met only
  for Tactics-owned scenario documents.
- **Movement model/kit/clip roundtrip:** unchanged and separately evidenced by the Movement
  readiness receipt. This review does not waive that independent gate.
- **Static manifest shape:** met as a local builder/test artifact; it is not proof of an
  available immutable diagram version or presentation.

## Smallest Tactics-owned delta using the existing contract

No new namespace or schema is needed. The smallest complete producer slice is:

1. Add a Tactics server-side/session-aware entry point that accepts the short-lived
   `authoringUrl`/`sessionId` issued by Training. The browser may carry the opaque session
   context, but must not hold the `tactics:publish` service credential.
2. Add the Tactics client/server calls for the already-defined session context: load the
   session, create/select/edit the local scenario, and preserve the session return target.
   For `select`, the client needs the existing Training diagram/version/presentation listing
   and read path rather than treating a local scenario id as a published reference.
3. Add the existing Movement publication worker flow behind the Tactics server boundary:
   build the manifest, call Movement `versions:allocate`, PUT each presigned asset, call
   `diagram-versions/:id:finalise`, and poll/read availability. The resulting immutable
   diagram version/presentation must be the only completion result.
4. Resolve the authoring session server-to-server with the exact
   `TacticsPresentationRefV1` and redirect to the session's return URL. Training then reads
   the resolved session outcome and stores its own reference. A browser query string or a
   Tactics `/v1/scenarios/{id}` URL alone is not sufficient.
5. Add one end-to-end receipt covering create/select, a returned session, immutable version
   availability, exact presentation selection, redirect, and Training-side reload/preview;
   retain the separate Movement asset/model/kit/clip receipt.

This keeps Tactics editable scenario storage and the immutable Movement publication boundary
separate, uses the already-described Training routes/scopes, and leaves the athlete runtime
integration unchanged. The first blocker to remove is the authorized `tactics:publish`
service credential plus a Tactics server/proxy path; client-only calls would expose the
credential and cannot satisfy server-side session resolution.

## Evidence commands

- `rg` across `src`, `api`, `tools`, `docs` for `authoring-session`, `manifestUrl`,
  `TacticsPresentationRef`, `allocate`, `finalise`, `resolve`, `returnUrl`, and `publish`.
- `Invoke-WebRequest` against the hosted root, served JS bundle, hosted `/v1/...` probes, and
  the known Movement API base.
- Source checked at local Tactics `a1f6c2d` and hosted stamp `muntizzx 4b80c99`.






