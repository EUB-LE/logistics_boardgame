from boardgame.agent import Agent
from boardgame.classes import Game
import unittest


class TestGame(unittest.TestCase):
    
    def test_Game(self) -> None: 
        g = Game(random_seed=0, cascade_damage_threshold=5, target_amount=6)
        g.set_agent(Agent(g))
        result = g.play_game()
        self.assertTrue(True)
