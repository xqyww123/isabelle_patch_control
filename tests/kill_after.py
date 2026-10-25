"""Test helper: run apply or unapply and die right after the k-th file was moved into the tree.
Usage: kill_after.py <k> apply|unapply <tree> <features.d>"""
import os
import sys
from pathlib import Path

from isabelle_patch_control import api
from isabelle_patch_control.engine import Replayer

k, command, tree, features_d = int(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
moved = 0
install = Replayer.install


def dying_install(self, *args):
    global moved
    install(self, *args)
    moved += 1
    if moved == k:
        os._exit(9)


Replayer.install = dying_install
res = (api.apply if command == "apply" else api.unapply)(tree, features_d)
sys.exit(res.exit_code)
