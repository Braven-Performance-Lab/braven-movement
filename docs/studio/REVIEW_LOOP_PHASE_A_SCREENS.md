# Braven Studio review loop, phase A: the screens

This is the design reference for the screens of specification 4, phase A (the Braven Studio
review loop, agreed by the owner on 12 November 2026). It says what each screen must show and
why. The screenshots that go with a change are made by `athlete/viewer/tests/review-browser.mjs`
and are not in git.

The screens belong to **hosted Studio** only. Local Studio (port 5397) keeps its screens: it has
no sign-in, and it shows no comment from the team.

## Rules for all the screens

- **The design language is Studio's own.** The colours, the type sizes, the 44 px controls and
  the 8 px corners come from `athlete/viewer/src/style.css`. No new colour family is added. The
  four comment kinds use four colours that Studio has already: amber-brown `#8c541a` (looks
  wrong), red-brown `#90382a` (technique is wrong), blue `#2f5f8a` (question, the one new
  colour) and Studio green `#08756c` (approve).
- **A kind is never told by colour only.** Each comment shows its kind in words, and each
  marker has a label with the kind, the time and the author.
- **Words are plain.** A coach reads "Looks wrong", "Left knee" and "¾ view", not an id.
- **Phone, tablet and desktop.** The layout follows Studio's four breakpoints. On a phone the
  stage is first, then the library, then the inspector with the Review tab.

## Screen 1: sign-in

Shown over all of Studio when nobody is signed in. Requirement ACC-2.

| State | What it shows |
| --- | --- |
| Ask | One field for the email address and one button, "Mail me a sign-in link". The text says that Studio is by invitation only and that the account is the one of Braven Tactics. There is no password field and no sign-up. |
| Link sent | "Check your mail", with the address the link went to, and a way to use another address. |
| Confirm the address | Shown when the link is opened on a device that did not ask for it. The person types the address again. |
| Not invited | "You cannot come in yet", the reason in words, the address that is signed in, and two buttons: try again, or use another address. |

Rules:

- Studio asks the server for no athlete file and no comment before the person is admitted.
- The sign-in code leaves the address bar after one use.
- A refusal is a sentence the person can act on. It never shows a code only.

## Screen 2: Studio for a signed-in person

- The header shows the person's name and role (Reviewer, Author or Owner) and a "Sign out"
  button, in the place of the "Local workspace" label.
- Hosted Studio shows no download link, because the published version serves no file to
  download.
- The private notes of the Review tab stay, with the heading "Private notes on this browser"
  and the statement that the team does not read them.

## Screen 3: the Review tab

Requirements FBK-1, FBK-2, FBK-4, FBK-6, SAFE-1 and SAFE-4. From top to bottom:

1. **The animation and its source check**, as local Studio shows them.
2. **The version line:** "Version 3e52b384 · revision 9". The first 8 characters of the
   version hash, with the full hash in the tooltip.
3. **The approval line.** Grey: "No reviewer approved this animation in this version."
   Green: "Approved in this version by <names>." It is green only when a reviewer approved this
   animation in the version on screen (SAFE-1). An approval of another version, of another
   animation, or by a person who is not a reviewer does not make it green.
4. **The comment form.**
   - The moment: "At 0.62 s". It follows the playhead. "Start a range here" marks the start;
     the person then moves the playhead to the end, and the line reads "From 0.85 s to 1.15 s".
   - The kind: four options, one choice. "Approve" is switched off for a person who is not a
     reviewer.
   - The comment text. It is optional for an approval only.
   - Body part (optional): the parts of this version's rig in a coach's words, and the ball.
   - Phase (optional): filled in from the playhead, and the person can change it.
   - Camera: the named view, or "Own angle" after the person moved the camera. Studio records
     the camera position with the comment.
   - One primary button, "Add comment", and the statement that a comment cannot be changed or
     deleted, only answered.
5. **The comments of this version**, oldest first. Each shows the kind, the time (a button
   that goes to that moment), the text, the marks, the author and the date, the answers, and a
   field to answer.
6. **Comments of earlier versions**, closed by default, each with its version. They have no
   button to a moment, because they are not about the version on screen (SAFE-4).

A movement that is not an animation of the published version takes no comment: a live Tactics
preview, and the receive-and-pass sequence that Studio builds. The form is replaced by one
sentence that says why, and no approval line is shown.

## Screen 4: the timeline

Requirement FBK-5.

- Each comment of the version on screen is a marker above the timeline track, at its time.
- A comment on one moment is a dot. A comment on a range is a bar from its start to its end.
- A marker goes to its moment, opens the Review tab and highlights its comment.
- The Review tab shows the number of comments on this version.
- Comments of earlier versions are never on the timeline.

## What phase A does not show

Drawing on a frame, attached pictures or video, the queue with its states, the comparison of
two versions, and blind grading are phase B and later. No screen here suggests them.
