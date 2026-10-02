"""Direct runtime checks of the small public example."""

import importlib.util
import warnings
from pathlib import Path

import pytest

pytestmark = pytest.mark.runtime


@pytest.fixture
def example():
    path = Path(__file__).resolve().parents[1] / "examples" / "core_model.py"
    spec = importlib.util.spec_from_file_location("core_example", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registration_collection_and_conservation(example):
    model = example.TransferModel(population=4, initial_wealth=3)
    agents = list(model.agents)
    assert len(agents) == 4
    assert len({agent.unique_id for agent in agents}) == 4
    assert all(agent.model is model for agent in agents)
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        warnings.simplefilter("error", FutureWarning)
        for _ in range(5):
            model.step()
            assert model.total_wealth() == 12
            assert all(agent.wealth >= 0 for agent in model.agents)
    assert model.steps == 5
    assert model.datacollector.model_vars == {
        "time": [0, 1, 2, 3, 4, 5], "total": [12] * 6,
    }
    collected = model.datacollector.get_agent_vars_dataframe()
    assert len(collected) == 4 * 6
    assert collected.groupby(level=0)["wealth"].sum().tolist() == [12] * 6


def test_seed_replays_full_agent_trajectory(example):
    histories = []
    for seed in (17, 17, 18):
        model = example.TransferModel(seed=seed)
        for _ in range(10):
            model.step()
        histories.append(model.datacollector.get_agent_vars_dataframe())
    assert histories[0].equals(histories[1])
    assert not histories[0].equals(histories[2])
    assert histories[0]["wealth"].nunique() > 1


def test_single_trader_and_zero_wealth_boundaries(example):
    for population, wealth in [(1, 5), (3, 0)]:
        model = example.TransferModel(population, wealth)
        model.step()
        assert [agent.wealth for agent in model.agents] == [wealth] * population


@pytest.mark.parametrize("kwargs", [{"population": 0}, {"population": 1.5},
                                   {"population": True}, {"initial_wealth": -1}])
def test_invalid_inputs(example, kwargs):
    with pytest.raises(ValueError):
        example.TransferModel(**kwargs)
