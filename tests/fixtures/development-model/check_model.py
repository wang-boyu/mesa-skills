"""Retained hand-derived and integrated checks for the disposable exercise."""

import copy
import subprocess
import sys
from pathlib import Path

from transfer import TransferModel


def test_one_transfer_has_hand_derived_balances():
    model = TransferModel(population=2, wealth=0)
    donor, recipient = model.agents.to_list()
    donor.wealth = 2
    donor.give_to(recipient)
    assert (donor.wealth, recipient.wealth) == (1, 1)
    recipient.wealth = 0
    recipient.give_to(donor)
    assert (donor.wealth, recipient.wealth) == (1, 0)


def test_independent_same_seed_replay_with_observation_on_one_side(tmp_path):
    first = TransferModel(seed=41)
    second = TransferModel(seed=41)
    initial = first.observe()
    for step in range(6):
        state = first.observe()
        python_rng = first.random.getstate()
        numpy_rng = copy.deepcopy(first.rng.bit_generator.state)
        assert first.observe() == state
        first.export(tmp_path / "exports")
        assert first.observe() == state
        assert first.random.getstate() == python_rng
        assert first.rng.bit_generator.state == numpy_rng
        first.step()
        second.step()
        assert first.observe() == second.observe(), step
        assert sum(balance for _, balance in first.observe()) == 15
        assert all(balance >= 0 for _, balance in first.observe())
    assert first.history == second.history
    assert any(state != initial for state in first.history[1:])
    assert len(first.history) == 7


def test_repeated_exports_preserve_prior_result(tmp_path):
    model = TransferModel()
    first = model.export(tmp_path)
    contents = (first / "observations.json").read_bytes()
    model.step()
    second = model.export(tmp_path)
    assert first.name == "run-0001"
    assert second.name == "run-0002"
    assert (first / "observations.json").read_bytes() == contents
    assert (second / "observations.json").read_bytes() != contents


def test_computational_import_is_headless_and_does_not_run(tmp_path):
    outputs = tmp_path / "outputs"
    result = outputs / "run-0001" / "observations.json"
    script = """
import importlib.abc
import sys

sys.path.insert(0, sys.argv[1])

class RejectUI(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith(('solara', 'mesa.visualization')):
            raise AssertionError(f'UI import: {fullname}')

sys.meta_path.insert(0, RejectUI())
import mesa

def reject_construction(*args, **kwargs):
    raise AssertionError('model construction during import')

mesa.Model.__init__ = reject_construction
from transfer import TransferModel
assert not any(name.startswith('solara') for name in sys.modules)
"""
    for previous_result in (False, True):
        if previous_result:
            result.parent.mkdir(parents=True)
            result.write_bytes(b"previous result\n")
        before = {
            path.relative_to(outputs): path.read_bytes() if path.is_file() else None
            for path in outputs.rglob("*")
        }
        checked = subprocess.run(
            [sys.executable, "-c", script, str(Path(__file__).resolve().parent)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert checked.returncode == 0, checked.stderr
        assert checked.stdout == checked.stderr == ""
        assert outputs.exists() == previous_result
        assert {
            path.relative_to(outputs): path.read_bytes() if path.is_file() else None
            for path in outputs.rglob("*")
        } == before
