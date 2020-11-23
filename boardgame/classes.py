from __future__ import annotations
from boardgame.player_actions import ACTIONS, InvalidActionException, PlayerAction
from typing import TYPE_CHECKING
from boardgame.agent import Agent
from boardgame.config import *
import json
import random
import math
import logging

if TYPE_CHECKING:
    from boardgame.player_actions import get_valid_player_actions

class Game():
    def __init__(self, random_seed:int = None) -> None: 
        if random_seed:
            random.seed(random_seed)
        self.cascade_level:int = 0
        self.destruction_level:int = 0
        self.damage_cards:list[int] = _create_and_shuffle_damage_cards()
        self.damage_cards_discards:list[int] = []
        self.player_cards:list[int] = _create_and_shuffle_player_cards()
        self.player_cards_discards:list[int] = []
        self.players:list[Player] = [
            Player(type=PLAYER_TYPE_INDUSTRY),
            Player(type=PLAYER_TYPE_INVESTOR),
            Player(type=PLAYER_TYPE_DRIVER), 
            Player(type=PLAYER_TYPE_DRIVER)
        ]
        self.active_player_id:int = 0
        self.nodes:list[Node] = _load_nodes_from_json()
        self.turn = 0
        self.start_node_id:int = TARGET_START_NODE 
        self.end_node_id:int = TARGET_END_NODE
        self.target_freight:int = TARGET_AMOUNT
        self.damage_card_stack_was_empty = False

        # damage nodes at start 
        for damage_points in range (1,4): 
            node_index = self.damage_cards.pop(0)
            #TODO change indexes to start at 0 and correspond to array positions
            if node_index in range(1, len(self.nodes) + 1):
                self.nodes[node_index].damage = damage_points
            self.damage_cards_discards.append(node_index)
        
        # set player founds and position at start
        for player in self.players:
            player.funds = 2 
            player.location_id = self.start_node_id

        # position two freight units at start 
        self._get_node_by_id(self.start_node_id).freight = 2
    
    def set_agent(self, agent: Agent) -> None:
        self.agent = agent

    def _get_player_by_id(self, id:int) -> Player:
        return next(player for player in self.players if player.id == id)
    
    def _get_node_by_id(self, id:int) -> Node:
        return next(node for node in self.nodes if node.id == id)

    def _add_damage_to_node(self, node_id:int, damage_value:int) -> None: 
        node =  self._get_node_by_id(node_id)
        node.damage += damage_value
        logging.info(f"Node {node_id} ({node.name}) receives {damage_value} damage (now has {node.damage})")
        if node.damage > 3:
            node.damage = 3
            self._cascade_node(node_id=node_id)
    
    def _cascade_node(self, node_id:int) -> None: 
        node = self._get_node_by_id(node_id)
        node.affected_by_cascade = True
        self.cascade_level += 1
        logging.info(f"Node {node_id} ({node.name}) is affected by a cascade. Cascade level is now {self.cascade_level}.")
        if self.cascade_level >= 6: 
            raise GameLostException(f"Cascade level is {self.cascade_level}, but is only allowed to be max. 5.")  
        for neighbor_node_id in node.neighbors:
            neighbor_node = self._get_node_by_id(neighbor_node_id)
            if not neighbor_node.affected_by_cascade:
                self._add_damage_to_node(neighbor_node_id, 1)
        node.affected_by_cascade = False
    
    def _get_next_player_id(self) -> int:
        return self.players[(self.active_player_id + 1) % len(self.players)].id
    
    def play_game(self) -> None: 
        while True:
            try: 
                self.play_turn()
                self.turn += 1
            except GameLostException as e: 
                logging.info(f"Game lost: {e.reason}")
                return False 
            except GameWonException as e:
                logging.info(F"Game Won: {e.message}")
                return True
    
    def play_turn(self) -> None:
        self.action_phase()
        self.resupply_phase()
        self.damage_phase()
        self.active_player_id = self._get_next_player_id()
    
    def action_phase(self) -> None: 
        logging.info(f"Start action phase.")
        player = self._get_player_by_id(self.active_player_id)
        logging.info(f"Player Status: {player.__dict__}")
        player.actions_left = 4 

        while player.actions_left > 0:
            if self.agent:
                try: 
                    action = self.agent.get_next_action_for_player(self.active_player_id)
                    action.run()
                except InvalidActionException as e:
                    logging.warning(f"Invalid Action {action.action.__name__}. Doing nothing instead.")   
                    self.agent.action_queues[self.active_player_id] = []
                    PlayerAction(self, self.active_player_id, ACTIONS[DO_NOTHING_ACTION_NAME]) 
                finally:
                    player.actions_left -= 1
            else:
                vpa = get_valid_player_actions(self, player.id)
                vpa[random.randint(0, len(vpa)-1)].run()
                player.actions_left -= 1
        # check win condition
            if self._get_node_by_id(self.end_node_id).freight >= self.target_freight:
                raise GameWonException()
        

    def resupply_phase(self) -> None: 
        logging.info(f"Start resupply phase.")
        self.draw_player_card()

    def damage_phase(self) -> None: 
        logging.info(f"Start damage phase.")
        destruction_level_to_card_draw_mapping = {0:1, 1:1, 2:2, 3:2, 4:3}
        card_draw_due_to_descruction = destruction_level_to_card_draw_mapping[self.destruction_level]
        logging.info(f"Draw {card_draw_due_to_descruction} cards due to destruction level {self.destruction_level}.")
        for i in range(0, card_draw_due_to_descruction):
            self.draw_damage_card()
    
    def draw_player_card(self, draw_from:str = 'top') -> None: 
        player = self._get_player_by_id(self.active_player_id)
        if draw_from not in ['top', 'bottom']:
           raise ValueError("from parameter must be 'top' or 'bottom'.") 
        if len(self.player_cards) == 0:
            raise GameLostException("No player cards left.")
        if draw_from is "top":
            card = self.player_cards.pop()
        else:
            card = self.player_cards.pop(0)
        logging.info(f"Player {player.name} draws ({card}) from the {draw_from} of the player card stack.")
        self.player_cards_discards.append(card)

        if card == 1:
            player.funds +=1
            logging.info(f"Player {player.name} receives 1 fund (now has {player.funds}).")
        else:
            self.destruction_level += 1
            logging.info(f"Destrution level increased to {self.destruction_level}. Drawing a damage card.")
            self.draw_damage_card(damage_to_node=3)
            random.shuffle(self.damage_cards_discards)
            self.damage_cards += self.damage_cards_discards
            self.damage_cards_discards = [] 
            logging.info(f"Shuffle damage card discard stack and put it on top of the damage card stack.")
               
    def draw_damage_card(self, draw_from:str = 'top', damage_to_node:int=1) -> None: 
        player = self._get_player_by_id(self.active_player_id)
        if draw_from not in ['top', 'bottom']:
            raise ValueError("from parameter must be 'top' or 'bottom'.")     
        try:
            if draw_from is "top":
                card = self.damage_cards.pop()
            else:
                card = self.damage_cards.pop(0)
            self.damage_cards_discards.append(card)
            logging.info(f"Player {player.name} draws ({card}) from the {draw_from} of the damage card stack.")
            if card is not 0:
                self._add_damage_to_node(node_id=card, damage_value=damage_to_node)
        except IndexError:
            logging.info("The damage card stack is empty. The next time the damage card are restocked, a card will be drawn and 3 damage points will be added to that note.")
        
    
    
    

        
       
class Node(): 
    def __init__(self, id:int, name:str, node_type:str, neighbors:list[int]) -> None: 
        self.id = id
        self.name = name
        self.node_type = node_type
        self.neighbors = neighbors
        self.damage = 0 
        self.freight = 0
        self.affected_by_cascade = False      

class Player():
    id_counter = 0    

    def __init__(self, type:str, location_id:int=1, funds:int=0) -> None:
        self.id = Player.id_counter
        self.name = f"{type} (ID: {self.id})"
        self.type = type
        self.location_id = location_id
        self.funds = funds
        self.actions_left = 4 

        Player.id_counter += 1        
    
    def __dir__(self) -> list:
        return ['id', 'name', 'type', 'location_id', 'funds', 'actions_left']


def _load_nodes_from_json(path_to_json:str = "boardgame/res/map.json") -> list[Node]: 
        """Loads a list of nodes from a json file

        Args:
            path_to_json (str, optional): [description]. Defaults to "boardgame/map.json".

        Returns:
            list[Node]: [description]
        """
        with open(path_to_json) as f:
           data = json.load(f)
        result = [] 
        for entry in data: 
            result.append(Node(**entry))
        return result

def _create_and_shuffle_damage_cards() -> list[int]:
    """Emulate a shuffled standard deck of 1 to 21 with two jokers (=0) and only one color

    Returns:
            list[int]: shuffled standard deck of 23 cards
    """
    damage_cards = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 0, 0, 0, 0, 0]
    random.shuffle(damage_cards)
    return damage_cards

def _create_and_shuffle_player_cards(number_of_fund_cards:int = 56, number_of_damage_cards:int = 4) -> list[int]: 
    """Shuffle damage cards (0) into fund cards in such a way that they can only occur one time for each step_size 

     Args:
            number_of_fund_cards (int, optional): [description]. Defaults to 56.
            number_of_damage_cards (int, optional): [description]. Defaults to 4.

     Returns:
            list[int]: list where 1 represents a fund card and 0 represents a damage card. 
    """
    player_cards = [1 for x in range(number_of_fund_cards)]
    step_size = math.ceil(number_of_fund_cards / number_of_damage_cards)
    for x in range(0,number_of_damage_cards): 
        player_cards.insert(random.randint(x * step_size, (x+1) * step_size),0)
    return player_cards

class GameLostException(Exception):
    def __init__(self, reason):
        self.reason = reason

class GameWonException(Exception): 
    def __init__(self, message = "GAME WON"):
        self.message = message
