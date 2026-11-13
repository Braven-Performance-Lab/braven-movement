# Braven Studio review loop, phase B: the plan

Written by the Studio lane on 13 November 2026, for Main and the owner. It is a plan. No phase B
code exists, and nothing in it is decided before the owner agrees.

**Source.** Specification 4 (the Braven Studio review loop), sections 4 to 6 and 8, and
specification 2 (coach review and agreement), requirements AGR-1, APR-1 and APR-2. Phase A is on
main in pull requests 147, 148, 149 and 160, read at main `0cbc254`.

**What phase B is.** A coach sees a comment become a tracked item, is told when it is fixed,
compares the old and the new version, closes or reopens the item, and approves. The
requirements are FBK-3, FBK-7, QUE-1 to QUE-5 and VER-1 to VER-6, with SAFE-2.

## 1. Where phase A stands

- All phase A code is on main. A preview is deployed
  (`https://braven-studio.developer-78c.workers.dev`), with its D1 database and its private R2
  bucket.
- **Phase A is not proved on the real services.** No person signed in on the preview yet, no
  file went to R2, and no trigger ran on the real database. Phase B must not start on the
  server side before that proof, because phase B builds on the same sign-in, the same bucket
  and the same triggers.

## 2. What phase B reuses from phase A

| Phase A part | File | Use in phase B |
| --- | --- | --- |
| Token check, admission, three roles | `athlete/studio-api/src/firebase.mjs`, `people.mjs` | Unchanged. Each new route calls `requireRole`. |
| The record of each act | `http.mjs` (`event`), table `events` | Each state change of an item writes an event in the same batch. |
| Versions named by the manifest hash, draft and published, owner-only publication | `versions.mjs`, table `versions` | This is VER-1 and QUE-5 already. Phase B adds which items a version answers. |
| Append-only comments with answers | `comments.mjs`, table `comments`, the triggers | An item points at its comment. A reopening is a new comment. |
| The `approve` comment, reviewer only, on a published version | `comments.mjs`, `comments.js` (`approvers`) | This is VER-5 already: an approval belongs to one animation in one version. |
| Comments of earlier versions in their own list | `comments.js` (`splitByVersion`) | The base for "review again": the item list reads the same split. |
| Sign-in, API client, hash check of each file | `athlete/viewer/src/session.js`, `review-api.js`, `athlete-source.js` | Unchanged. The second model of the comparison loads through the same checked path. |
| Review tab and Team dialog | `review-panel.js`, `team-panel.js` | The queue and the item state go into these two places. |
| Test stand-ins, mutation lists, development server, browser journey | `studio-api/tests/`, `viewer/tests/review-*.mjs`, `studio-api/tools/` | Each new guard gets a test and a mutation entry. The journey grows by the phase B steps. |

## 3. What is new

### 3.1 The queue (QUE-1, QUE-2, QUE-3, SAFE-2)

- **One item for each comment that asks for a change.** A comment of the kind "looks wrong" or
  "technique is wrong" makes an item at once. A "question" makes an item only when an author
  turns it into one. An "approve" makes none.
- **Tables (migration 0002):**
  - `items(id, comment_id, class, route, created_at)`. One row for each item. `class` is
    `defect`, `judgement` or not set yet. `route` is `engine-technique`, `athlete-animation`,
    `athlete-model` or `studio`.
  - `item_events(id, item_id, at, actor_uid, state, reason, version_id)`. Append-only, with the
    same triggers as `comments`. The state of an item is its newest event. No row of `items`
    changes after the class and the route are set.
- **States:** new, accepted, in work, ready for review, closed, declined. A declined item needs
  a reason. A "ready for review" event names the version that answers the item.
- **Who moves an item:** an author accepts, declines, takes in work and marks ready. The
  reviewer who made the comment closes or reopens. The owner can do each of these.
- **Class (QUE-2, SAFE-2):** an author sets the class. A `judgement` item cannot go to "in
  work" before the owner rules on it. The ruling is an event of the owner on the item. The
  server refuses the transition without it, and a test proves the refusal.
- **Route (QUE-3):** the first route comes from the manifest. A clip of the kind `technique`
  goes to the engine technique, and a clip of the kind `general` goes to the athlete
  animation. An author can change the route. The item screen says which route an item has,
  because a technique change is slower than a clip change (specification 4, section 11).

### 3.2 Versions and review again (VER-2, VER-3, VER-4, VER-6)

- **Told when it is ready (VER-2).** First step: no mail. When a reviewer opens Studio, the
  Review tab shows "Ready for your review" with each of their items that has a "ready for
  review" event. One press loads the answering version at the comment's time. Mail is a
  separate decision (section 5, decision B2), because it needs a mail provider and a secret.
- **Old and new side by side (VER-3).** This is the largest client change of phase B. Today
  `athlete/viewer/src/main.js` holds one model in module variables. The comparison needs two
  models in step: the version of the comment and the answering version. The plan is to move
  the model, the mixer and the ball into one object that can exist two times, and to draw the
  two with one renderer in two halves of the stage. Each model is about 17 MB, so a phone can
  be too small for two; the plan measures the memory on a phone before it offers the
  comparison there.
- **Close or reopen (VER-4).** The reviewer closes the item, or reopens it with a new comment
  on the new version. The new comment points at the same item, so the item keeps its history
  across versions, and no comment moves to a version it was not made on (SAFE-4).
- **The state of each animation (VER-6).** The library list shows for each animation: the
  version on screen, the number of open items, and who approved it in this version. The data
  is one read: `GET /api/animations?version=`.
- **Which items a version answers.** The "ready for review" event carries the version id.
  No new table is necessary for that.

### 3.3 Approvals (VER-5, and specification 2: APR-1, APR-2)

- Phase A has the rule already: an approval is an `approve` comment by a reviewer on one clip
  in one published version, and a later version starts with no approval.
- New in phase B: an approval needs **no open item** on that clip in that version, or the
  screen says that items are still open. That is a rule to agree (decision B5).
- APR-2 says that an approval lapses "when the build changes anything the figure shows".
  Specification 4 is stricter: each new version needs a new approval. The plan follows
  specification 4. It can carry an approval forward later for a clip whose own hash did not
  change (`jobSha256` in the manifest), if the owner wants that.
- Open point: ruling 12.9 makes the Studio approval the approval before publication of
  specification 2. Nothing connects Studio to the manual pipeline yet. That connection is not
  in this plan.

### 3.4 The agent interface (QUE-4, QUE-5)

- **What an agent does:** reads the queue, takes an item, gets the comment with its version,
  time, body part, camera and a picture of the frame, and returns either an answer (a
  question) or a draft version.
- **What an agent never does:** publish a version, approve, invite, or change a class. The
  owner-only publication of phase A stays (ruling 12.6).
- **How an agent signs in.** This is new and it is a security decision (decision B3). The
  plan: an author makes an **agent key** in the Team screen. The server keeps only the SHA-256
  of the key, the author who made it and its date. The key shows one time. A request with the
  key acts as "agent of that author", a fourth role with only the routes above. Each act of an
  agent writes an event with the key id and the author. The owner can revoke a key.
- **The picture of the frame.** The page makes it when the comment is added (Studio has
  "Capture" already) and stores it in the private bucket as `comments/<comment id>.png`. It is
  a picture of the model, not of a person.

### 3.5 Drawing and attachments (FBK-3)

- **Drawing on a paused frame:** strokes over the frame picture, stored as a second picture
  beside it. No person is in it.
- **A picture or a short video on a comment:** this is uploaded media, and it can show real
  athletes, some of them minors. The consent rule (NEW-3, SAFE-3) is phase C. The plan
  recommends that phase B takes the drawing only, and that attached pictures and video wait
  for the consent rule (decision B4).

### 3.6 Blind grading (FBK-7)

- Phase A shows each reviewer the comments of all. A reviewer who grades a build blind must
  not see them first.
- Ruling 11.2 of specification 2 keeps the blind marks in the Client Zone, not in Studio. So
  Studio only needs to know that a reviewer has an open blind pack for a version.
- The plan: `blind_holds(reviewer_uid, version_id, set_by, set_at, released_at)`. The owner
  sets a hold when a pack goes out and releases it when the marks are in. While a hold is
  open, the comment routes give that reviewer only their own comments on that version, and the
  timeline shows only their own markers. The server does the filter, and a test proves that a
  held reviewer cannot read another person's comment by any route.
- Open point: who sets and releases the hold in practice, and whether the Client Zone can do
  it by itself (decision B6).

## 4. The order of the work

Each line is one change from main, with its tests first, its mutation entries, and screenshots
for a screen change. The sizes are relative; I did not measure a duration.

| Change | Content | Size | Needs first |
| --- | --- | --- | --- |
| B1 | Queue on the server: migration 0002, items, item events, class, route, the judgement refusal | Medium | The phase A proof on the preview |
| B2 | Queue on the screen: item state on each comment, the queue list for an author, class and route controls | Medium | B1 |
| B3 | Ready for review, load the answering version at the comment's time, close and reopen | Medium | B2 |
| B4 | The state of each animation in the library (VER-6), and the open-item rule for an approval | Small | B3, decision B5 |
| B5 | Old and new side by side | Large | B3. The refactor of `main.js` is its own change first. |
| B6 | Agent keys and the agent routes, frame pictures | Large | B1, decision B3 |
| B7 | Blind holds | Medium | Decision B6 |
| B8 | Drawing on a frame | Medium | B6 (the frame picture) and decision B4 |

After B1 to B4 a coach has the whole loop without the comparison: comment, item, new version,
review again, close, approve. That is the first point at which phase B is usable.

## 5. Decisions for the owner

| No. | Decision | Recommendation |
| --- | --- | --- |
| B1 | Does phase B wait for the phase A proof on the preview (a real sign-in, upload and comment)? | Yes. |
| B2 | How is a reviewer told that an item is ready: in Studio only, or by mail too? | In Studio first. Mail later, because it needs a mail provider and a secret. |
| B3 | May an agent work through a key that an author makes, with a role that cannot publish or approve? | Yes, with the key kept as a hash, shown one time, and each act recorded. |
| B4 | Does phase B take attached pictures and video on a comment, or the drawing only? | The drawing only. Attached media waits for the consent rule of phase C. |
| B5 | Can a reviewer approve an animation while it has open items in that version? | No. The screen names the open items. |
| B6 | Who sets and releases a blind hold: the owner by hand, or the Client Zone? | The owner by hand first. |
| B7 | Who releases a new version: the owner only (as phase A), or an author too? | The owner only, until a second person asks for it. |

## 6. Risks and what is not known

- **Phase A on the real services is not proved.** D1 and R2 can behave in a way the stand-ins
  do not show.
- **The comparison on a phone.** Two models at one time can be too much memory. Not measured.
- **`main.js` is one large module.** The refactor for two models touches the code that local
  Studio uses too. The 45 checks of the local browser test are the guard.
- **Agent keys are a new kind of credential.** A leaked key acts as an author's agent until it
  is revoked. The role limits what it can do, and the events show what it did.
- **The browser journeys do not run in CI.** They need Chrome, the athlete folder and the
  Tactics checkout. Phase B adds page code that only these journeys cover.
- **Open notes from the phase A reviews** go into B2: the Team lists can show an older answer
  when two reads overlap, a marker under the playhead is hard to see, and no test covers the
  two sentences for a failed access check.
- **Not read for this plan:** the code of the Client Zone, and how the manual pipeline reads an
  approval. Sections 3.3 and 3.6 name the two as open points.
