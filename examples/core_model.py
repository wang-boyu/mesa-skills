"""Small conserving-transfer model for demonstrating Mesa 3.5 APIs."""

import json

import mesa
from mesa.datacollection import DataCollector


class Trader(mesa.Agent):
    """Transfer one unit to another trader when a positive balance permits it."""

    def __init__(self, model, wealth):
        super().__init__(model)
        self.wealth = wealth

    def step(self):
        others = [agent for agent in self.model.agents if agent is not self]
        if self.wealth > 0 and others:
            recipient = self.random.choice(others)
            self.wealth -= 1
            recipient.wealth += 1


class TransferModel(mesa.Model):
    """Sequential random activation with initial and post-step observations."""

    def __init__(self, population=6, initial_wealth=10, seed=7):
        if type(population) is not int or population < 1:
            raise ValueError("population must be a positive integer")
        if type(initial_wealth) is not int or initial_wealth < 0:
            raise ValueError("initial_wealth must be a non-negative integer")
        super().__init__(rng=seed)
        Trader.create_agents(self, population, wealth=initial_wealth)
        self.datacollector = DataCollector(
            model_reporters={"time": "time", "total": self.total_wealth},
            agent_reporters={"wealth": "wealth"},
        )
        self.datacollector.collect(self)

    def total_wealth(self):
        return sum(agent.wealth for agent in self.agents)

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)


if __name__ == "__main__":
    model = TransferModel()
    for _ in range(8):
        model.step()
    print(json.dumps(model.datacollector.model_vars))
