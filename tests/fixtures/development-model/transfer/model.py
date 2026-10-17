"""Coordination and observations for the synthetic transfer model."""

import json

from mesa import Model

from .agents import Trader
from .run_output import allocate_run_directory


class TransferModel(Model):
    def __init__(self, population=5, wealth=3, seed=41):
        super().__init__(rng=seed)
        Trader.create_agents(self, population, wealth=wealth)
        self.history = [self.observe()]

    def observe(self):
        return tuple((agent.unique_id, agent.wealth) for agent in self.agents)

    def step(self):
        self.agents.shuffle_do("step")
        self.history.append(self.observe())

    def export(self, root="outputs"):
        destination = allocate_run_directory(root)
        (destination / "observations.json").write_text(json.dumps(self.history) + "\n")
        return destination
