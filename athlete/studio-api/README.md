# Braven Studio API

The backend of the Braven Studio review loop, phase A (specification 4). It is a Cloudflare
Worker with a D1 database and a private R2 bucket. **It is not deployed.** The Cloudflare
resources, the subdomain and the deploy need the owner's yes on the lane board.

## What it does

| Requirement | How |
| --- | --- |
| ACC-2 | A request passes only with a Firebase ID token that verifies, from a person who is a member or whose verified email has an open invitation. There is no sign-up route. |
| ACC-3 | Each member has one role: reviewer, author or owner. A reviewer is told that a draft version does not exist. |
| ACC-4 | The token comes from the Firebase project that Braven Tactics uses. The uid is the same person in the two products. |
| ACC-5 | Each act writes a row in `events` in the same batch as the act. |
| FBK-1, FBK-2 | A comment holds the clip, the version (the sha256 of the manifest), the model sha256, a time or a time range, and optionally a body part, a phase name and a camera view. |
| FBK-4 | The kinds are `looks-wrong`, `technique-wrong`, `question` and `approve`. |
| FBK-6, SAFE-4 | There is no route to change or delete a comment, and database triggers refuse an UPDATE or a DELETE. An answer is a new comment under the first. |
| SAFE-1 | Only a reviewer can make an `approve` comment, and only on a published version. |
| Ruling 12.6 | Only the owner role publishes a version. |

## Routes

All routes are under `/api/`. All but `health` need `Authorization: Bearer <Firebase ID token>`.

| Route | Who | Purpose |
| --- | --- | --- |
| `GET /api/health` | anybody | The service answers. |
| `GET /api/me`, `PATCH /api/me` | member | The caller's role. Set the name others see. |
| `GET /api/people` | owner | Members and open invitations. |
| `POST /api/invitations` `{email, role}` | owner | Invite an address into a role. |
| `DELETE /api/invitations/<email>` | owner | Revoke an open invitation. |
| `POST /api/people/<uid>/remove` | owner | Remove a member. The last owner stays. |
| `GET /api/versions` | member | The versions the caller may see, and the current one. |
| `PUT /api/versions` (manifest bytes) | author, owner | Record a draft version. The answer gives its id. |
| `PUT /api/versions/<id>/files/<name>` | author, owner | Store the model or the library of a draft. The bucket checks the sha256. |
| `POST /api/versions/<id>/publish` | owner | Publish a draft that has all its files. |
| `GET /api/versions/<id>/files/<name>` | member | The manifest, the model or the library. |
| `GET /api/comments?version=&clip=` | member | Comments, oldest first. |
| `POST /api/comments` | member | Add a comment, or an answer with `{parentId, body}`. |

## Tests

The tests need Node 22.13 or later and nothing else. There is no `npm install`.

```bash
node --test "tests/*.test.mjs"
```

`python -m unittest discover -s tests` at the repository root runs them too
(`tests/test_studio_api.py`). The database in the tests is SQLite from Node with the migration
file applied, so the schema under test is the schema D1 gets. The tests do not prove D1's own
limits or R2's own behaviour: those need the deployed service.

```bash
node tests/mutations.mjs
```

This removes one guard at a time and makes sure that a test fails. It covers the guards in its
list and no others.

## On this machine

```bash
node tools/dev-server.mjs --athlete "<athlete output folder>"
```

This runs the same `handle()` as the Worker on `127.0.0.1:5398`, with the test stand-ins for D1 and R2, in memory. It also serves a stand-in for the Firebase sign-in service under `/dev-identity/`, which the Worker never has. It is for development and screenshots only. `tools/dev-studio.mjs` starts it together with the Studio page.

## Limits to know

- A coach signs in one time on Studio and one time on Tactics. The account is the same.
- To change a person's role, the owner removes the person and then invites the address again. An address that is an active member cannot be invited.
- A person can change the name that shows beside their comments, earlier comments included. Each change is a `member.renamed` row in `events` with the old and the new name.
- A read of comments returns 5000 rows at most. A longer list loses its oldest rows, and the answer has `truncated: true`.
- The first owner is an `invitations` row that a person adds to D1 at deploy time. It is not in git.
- A comment time must be inside the clip length that the manifest gives, plus one frame.
- There is no upload tool for a version yet. The development server uploads the athlete folder through the same routes at start.
