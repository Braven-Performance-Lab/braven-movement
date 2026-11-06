# Lane board: braven-movement

This repository runs on the lane board "braven-movement". Sessions working here are lanes on it: they post their work, questions and results to the board, and the owner answers there.

## Joining

The owner switches a session on by typing, in that session: `/board on <Lane> @braven-movement`, with a short, stable lane name. The session then follows the lane guide: https://github.com/Iron-Wire/mods/blob/main/lane-board/docs/LANE-GUIDE.md

## Setting up a repo

How each repo lands and is reviewed is set on the board's Settings tab: press **Set up** on the repo's card, answer its plain questions (who merges it, its CI, its tests, its screens, where it deploys), and Save. Each setting there links to its part of the guide: https://github.com/Iron-Wire/mods/blob/main/lane-board/docs/SETUP-GUIDE.md

## Who does what

- Lead lanes: Main.
- Service lanes: Train, Review, Deploy. They take requests from any lane.
- Finished, reviewed branches go to: Main.

## How a change moves

- One task or goal step is one change, on one branch: as big as it can be, as small as it needs to be. Never a change of its own for a one-line fix or a comment: it goes on the change it belongs to.
- A change grows on its branch until it lands: fixes, review findings and conflict fixes are new commits on the same branch. Never open a replacement branch or pull request.
- No stacking: start each branch from main, never on another branch that has not landed, yours or another lane's. A piece another lane needs lands first, on its own.
- Split a change only for a sensitive path, or when it grows too big to review. Each piece starts from main and lands on its own.
- At most 2 open changes per lane: one being reviewed or landed, one being built. At the limit, review, write tests or check your landed work: do not open more.
- Never watch CI yourself: no gh run watch, no --watch, no loop that asks GitHub again and again. The board reads CI for every lane and tells you once when CI on your change's commit has finished: end your turn and wait for its prompt.

The rules themselves come with the board, in each lane's prompt. Never put a password, key or token on the board.
