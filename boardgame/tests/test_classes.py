import unittest
import math
from boardgame.classes import PlayerAction, Game

class TestPlayerAction(unittest.TestCase):
    def test_player_action(self):
        pa = PlayerAction(print, "test")
        self.assertIsInstance(pa, PlayerAction)

class TestGame(unittest.TestCase):
    def setUp(self) -> None:
        self.game = Game(random_seed=0)
    
    def tearDown(self) -> None:
        self.game = None
    
    def test_create_and_shuffle_damage_cards(self) -> None:
        card_list = self.game.create_and_shuffle_damage_cards()
        self.assertIsInstance(card_list, list)
        for entry in card_list:
            self.assertIsInstance(entry, int)
        card_list_2 = self.game.create_and_shuffle_damage_cards()
        self.assertNotEqual(card_list, card_list_2)

    def test_create_and_shuffle_player_cards(self) -> None:
        number_of_fund_cards=56
        number_of_damage_cards=4
        player_cards = self.game.create_and_shuffle_player_cards(number_of_fund_cards, number_of_damage_cards)
        self.assertIsInstance(player_cards, list)
        for entry in player_cards:
            self.assertIn(entry, [0,1]) 
        # check that damage cards are distributed uniformly
        step_size =  math.ceil(player_cards / number_of_damage_cards)
        for i in range(0, number_of_damage_cards):
            slice = player_cards[i*step_size:(i+1)*step_size]
            self.assertIn(0, slice,"hi")