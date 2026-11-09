"""The scope guard of a locomotion rebake (athlete/verify_jog_asset.py).

The guard gained three relaxations for the gait rebuild: a clip may change
(--changed), a clip may be new (--added), and a mesh may take new skin weights
(--reskinned). Each relaxation must still refuse what it does not allow. The
data here is synthetic: two clips and one mesh, small enough to read.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'athlete'))

from verify_jog_asset import ScopeError, compare  # noqa: E402

CLIPS = {'Jog': {('foot_l', 'rotation'): ('LINEAR', (0.0, 1.0), (1, 0, 0, 0))},
         'Ready': {('pelvis', 'translation'): ('LINEAR', (0.0,), (0, 0, 1))}}
SHOE = [{'POSITION': ((0, 0, 0), (1, 0, 0)), 'JOINTS_0': ((1, 2, 0, 0),), 'WEIGHTS_0': ((0.6, 0.4, 0, 0),)}]


def clips(**changes):
    out = {k: dict(v) for k, v in CLIPS.items()}
    out.update(changes)
    return out


def shoe(**attributes):
    return {'shoes05': [dict(SHOE[0], **attributes)]}


NEW_JOG = {('foot_l', 'rotation'): ('LINEAR', (0.0, 1.0), (0.9, 0.1, 0, 0))}
RUN = {('foot_l', 'rotation'): ('LINEAR', (0.0, 0.5), (1, 0, 0, 0))}
NEW_WEIGHTS = ((1.0, 0, 0, 0),)


class Accepts(unittest.TestCase):
    def test_the_gait_rebuild(self):
        unchanged, reskinned = compare(CLIPS, clips(Jog=NEW_JOG, Run=RUN), shoe(), shoe(WEIGHTS_0=NEW_WEIGHTS),
                                       changed=['Jog'], added=['Run'], reskinned=['shoes05'])
        self.assertEqual(unchanged, ['Ready'])
        self.assertEqual(reskinned, ['shoes05'])


class Refuses(unittest.TestCase):
    def check(self, message, **kwargs):
        with self.assertRaises(ScopeError) as caught:
            compare(**kwargs)
        self.assertIn(message, str(caught.exception))

    def test_a_moved_vertex_on_a_reskinned_mesh(self):
        self.check('geometry changed', before=CLIPS, after=clips(Jog=NEW_JOG), mesh_before=shoe(),
                   mesh_after=shoe(WEIGHTS_0=NEW_WEIGHTS, POSITION=((0, 0, 0), (1, 0, 0.01))), reskinned=['shoes05'])

    def test_new_weights_on_a_mesh_not_named(self):
        self.check('skin weights changed', before=CLIPS, after=clips(Jog=NEW_JOG), mesh_before=shoe(),
                   mesh_after=shoe(WEIGHTS_0=NEW_WEIGHTS))

    def test_a_reskinned_name_that_matches_no_mesh(self):
        self.check('not in the before asset', before=CLIPS, after=clips(Jog=NEW_JOG), mesh_before=shoe(),
                   mesh_after=shoe(WEIGHTS_0=NEW_WEIGHTS), reskinned=['Athlete_Shoes'])

    def test_a_named_mesh_that_did_not_change(self):
        self.check('named as reskinned but unchanged', before=CLIPS, after=clips(Jog=NEW_JOG), mesh_before=shoe(),
                   mesh_after=shoe(), reskinned=['shoes05'])

    def test_a_clip_both_changed_and_added(self):
        self.check('both changed and added', before=CLIPS, after=clips(Jog=NEW_JOG, Run=RUN), mesh_before=shoe(),
                   mesh_after=shoe(), changed=['Jog', 'Run'], added=['Run'])

    def test_an_unlisted_new_clip(self):
        self.check('differ from --added', before=CLIPS, after=clips(Jog=NEW_JOG, Run=RUN), mesh_before=shoe(),
                   mesh_after=shoe())

    def test_another_clip_changed(self):
        self.check('Ready changed outside the rebake', before=CLIPS,
                   after=clips(Jog=NEW_JOG, Ready={('pelvis', 'translation'): ('LINEAR', (0.0,), (0, 0, 2))}),
                   mesh_before=shoe(), mesh_after=shoe())

    def test_a_changed_clip_that_did_not_change(self):
        self.check('Jog did not change', before=CLIPS, after=clips(), mesh_before=shoe(), mesh_after=shoe())


if __name__ == '__main__':
    unittest.main()
