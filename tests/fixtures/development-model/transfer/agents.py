"""Agent-owned transfer decisions in the synthetic exercise."""

from mesa import Agent


class Trader(Agent):
    def __init__(self, model, wealth):
        super().__init__(model)
        self.wealth = wealth

    def give_to(self, recipient):
        if self.wealth > 0 and recipient is not self:
            self.wealth -= 1
            recipient.wealth += 1

    def step(self):
        others = [agent for agent in self.model.agents if agent is not self]
        if others and self.wealth > 0:
            self.give_to(self.random.choice(others))
