from boardgame.agent import Agent
from boardgame.classes import Game
import unittest


class TestGame(unittest.TestCase):
    
    def test_Game(self) -> None: 
        g = Game()
        g.set_agent(Agent(g))
        g.play_game()
        self.assertTrue(True)
