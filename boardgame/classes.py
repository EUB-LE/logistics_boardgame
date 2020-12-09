from __future__ import annotations
from boardgame.player_actions import ACTIONS, InvalidActionException, PlayerAction
from typing import TYPE_CHECKING
from boardgame.agent import Agent
from boardgame.config import *
import json
import random
import math
import logging

# enable import only for type checking to avoid recursive imports
if TYPE_CHECKING:
    from boardgame.player_actions import get_valid_player_actions

    
class Game():
    """Instance of the boardgame logic that holds all variables, like players, node status, etc. Provides methods to manipulate game variables and perform game operations. 
    """
    def __init__(self, random_seed:int = None, disable_logging:bool = False, **kwargs) -> None: 
        """Constructor of boardgame.classes.Game 

        Args:
            random_seed (int, optional): Custom seed for all random operation. Defaults to None.
            disable_logging (bool, optional): Set to true to disable logging, e.g. if many iterations are played at once. Defaults to False.
        """
        if disable_logging:
            logging.disable(100)
        # initialize parameters either from kwargs or if not present from config.py
        target_start_node_id = kwargs.get('target_start_node') if kwargs.get('target_start_node') else TARGET_START_NODE
        target_end_node_id = kwargs.get('target_end_node') if kwargs.get('target_end_node') else TARGET_END_NODE
        target_amount = kwargs.get('target_amount') if kwargs.get('target_amount') else TARGET_AMOUNT

        number_of_damage_card_jokers = kwargs.get('number_of_damage_card_jokers') if kwargs.get('number_of_damage_card_jokers') else NUMBER_OF_DAMAGE_CARD_JOKERS
        number_of_fund_cards = kwargs.get(' number_of_fund_cards') if kwargs.get(' number_of_fund_cards') else NUMBER_OF_FUND_CARDS
        number_of_destruction_cards = kwargs.get('number_of_destruction_cards') if kwargs.get('number_of_destruction_cards') else NUMBER_OF_DESTRUCTION_CARDS

        self.cascade_damage_threshold = kwargs.get('cascade_damage_threshold') if kwargs.get('cascade_damage_threshold') else CASCADE_DAMAGE_THRESHOLD
        self.cascade_max_level = kwargs.get('cascade_max_level') if kwargs.get('cascade_max_level') else CASCADE_MAX_LEVEL

        
        if random_seed:
            random.seed(random_seed)
        self.cascade_level:int = 0
        self.destruction_level:int = 0
        self.damage_cards:list[int] = _create_and_shuffle_damage_cards(number_of_jokers=number_of_damage_card_jokers)
        self.damage_cards_discards:list[int] = []
        self.player_cards:list[int] = _create_and_shuffle_player_cards(number_of_fund_cards, number_of_destruction_cards)
        self.player_cards_discards:list[int] = []
        self.players:list[Player] = [
            Player(id = 0, type=PLAYER_TYPE_INDUSTRY),
            Player(id = 1, type=PLAYER_TYPE_INVESTOR),
            Player(id = 2, type=PLAYER_TYPE_DRIVER), 
            Player(id = 3, type=PLAYER_TYPE_DRIVER)
        ]
        self.active_player_id:int = 0
        self.nodes:list[Node] = _load_nodes_from_json()
        self.turn = 0
        self.start_node_id:int = target_start_node_id
        self.end_node_id:int = target_end_node_id
        self.target_freight:int = target_amount
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
        """Set the agent that determines the actions of the players, i.e. the strategy.

        Args:
            agent (Agent): Agent with reference to this Game.
        """
        self.agent = agent

    def _get_player_by_id(self, id:int) -> Player:
        """Get a reference to a player object by ID. 

        Args:
            id (int): player id

        Returns:
            Player: Player object. 
        """
        for player in self.players:
            if player.id == id:
                return player
    
    def _get_node_by_id(self, id:int) -> Node:
        """Get a reference to node object by ID.

        Args:
            id (int): node id

        Returns:
            Node: Node object
        """
        for node in self.nodes:
            if node.id == id:
                return node

    def _add_damage_to_node(self, node_id:int, damage_value:int) -> None: 
        """Internally called to add damage points to a node.

        Args:
            node_id (int): node id for the node where the damage will be applied
            damage_value (int): damage value
        """
        node =  self._get_node_by_id(node_id)
        node.damage += damage_value
        logging.info(f"Node {node_id} ({node.name}) receives {damage_value} damage (now has {node.damage})")
        if node.damage > self.cascade_damage_threshold:
            node.damage = self.cascade_damage_threshold
            self._cascade_node(node_id=node_id)
    
    def _cascade_node(self, node_id:int) -> None: 
        """Internally called to apply the cascade mechanism to a node.

        Args:
            node_id (int): node id for the node where the cascade happens

        Raises:
            GameLostException: If the cascade counter is more than the maximum allowed number of cascades.
        """
        node = self._get_node_by_id(node_id)
        node.affected_by_cascade = True
        self.cascade_level += 1
        logging.info(f"Node {node_id} ({node.name}) is affected by a cascade. Cascade level is now {self.cascade_level}.")
        if self.cascade_level > self.cascade_max_level: 
            raise GameLostException(GAME_LOST_STR_CASCADE)  
        for neighbor_node_id in node.neighbors:
            neighbor_node = self._get_node_by_id(neighbor_node_id)
            if not neighbor_node.affected_by_cascade:
                self._add_damage_to_node(neighbor_node_id, 1)
        node.affected_by_cascade = False
    
    def _get_next_player_id(self) -> int:
        """Internally called to determine the player for the next turn.

        Returns:
            int: Id of current player.
        """
        return self.players[(self.active_player_id + 1) % len(self.players)].id
    
    def play_game(self) -> dict: 
        """Starts the game and performs the game loop until the game is won or lost. 

        Returns:
            dict: Result dictionary containing the fields "turn", "result", and in case of a lost game "reason". 
        """
        while True:
            try: 
                self.play_turn()
                self.turn += 1
            except GameLostException as e: 
                logging.info(f"Game lost: {e.reason}")
                return {
                    "turn": self.turn,
                    "result": "LOST", 
                    "reason": e.reason
                } 
            except GameWonException as e:
                logging.info(F"Game Won: {e.message}")
                return {
                    "turn": self.turn, 
                    "result": "WON"
                }
    
    def play_turn(self) -> None:
        """Play a single turn of the game.
        """
        self.action_phase()
        self.resupply_phase()
        self.damage_phase()
        self.active_player_id = self._get_next_player_id()
    
    def action_phase(self) -> None: 
        """Play the action phase of a turn.

        Raises:
            GameWonException: If enough freight units are transported to the target node.
        """
        logging.info(f"Start action phase.")
        player = self._get_player_by_id(self.active_player_id)
        node = self._get_node_by_id(player.location_id)
        player.actions_left = 4 
        logging.info(f"Player Status: {player.__dict__}")
        logging.info(f"Node status: {node.__dict__}")
        

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
        """Play the resupply phase.
        """
        logging.info(f"Start resupply phase.")
        self.draw_player_card()

    def damage_phase(self) -> None: 
        """Play the damage phase.
        """
        logging.info(f"Start damage phase.")
        destruction_level_to_card_draw_mapping = {0:1, 1:1, 2:2, 3:2, 4:3}
        card_draw_due_to_descruction = destruction_level_to_card_draw_mapping[self.destruction_level]
        logging.info(f"Draw {card_draw_due_to_descruction} cards due to destruction level {self.destruction_level}.")
        for i in range(0, card_draw_due_to_descruction):
            self.draw_damage_card()
    
    def draw_player_card(self, draw_from:str = 'top') -> None: 
        """Draws a player card for the active player. 

        Args:
            draw_from (str, optional): Draw from either 'top' or 'bottom' of the deck. Defaults to 'top'.

        Raises:
            ValueError: If draw_from is neither 'top' or 'bottom'. 
            GameLostException: If all player cards are drawn.
        """
        player = self._get_player_by_id(self.active_player_id)
        if draw_from not in ['top', 'bottom']:
           raise ValueError("from parameter must be 'top' or 'bottom'.") 
        if len(self.player_cards) == 0:
            raise GameLostException(GAME_LOST_STR_CARDS)
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
        """Draws a damage card for the active player.

        Args:
            draw_from (str, optional): Draw from either 'top' or 'bottom' of the deck. Defaults to 'top'.
            damage_to_node (int, optional): Number of damage points that will be applied to the drawn node. Defaults to 1.

        Raises:
            ValueError: [description]
        """
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
    """Represents a node on the game board.
    """
    def __init__(self, id:int, name:str, node_type:str, neighbors:list[int]) -> None: 
        """Constructor of boardgame.classes.Node. 

        Args:
            id (int): Node Id.
            name (str): Node name. 
            node_type (str):  Node type should be either "green", "orange", or "purple". 
            neighbors (list[int]): List that contains the ids of neighboring nodes. 
        """
        self.id = id
        self.name = name
        self.node_type = node_type
        self.neighbors = neighbors
        self.damage = 0 
        self.freight = 0
        self.affected_by_cascade = False      

class Player():
    """Represents a player on the game board.
    """
    id_counter = 0    

    def __init__(self, id:int, type:str, location_id:int=1, funds:int=0) -> None:
        """Constructor for boardgame.classes.Player

        Args:
            id (int): Player Id.
            type (str): Player type should be either "DRIVER_PLAYER", "INDUSTRY_PLAYER", or "INVESTOR_PLAYER". See config.py
            location_id (int, optional): Id ot the node this player is currently located at. Defaults to 1.
            funds (int, optional): Amount of funds this player currently has. Defaults to 0.
        """
        self.id = id
        self.name = f"{type} (ID: {self.id})"
        self.type = type
        self.location_id = location_id
        self.funds = funds
        self.actions_left = 4 

        # automatic ID does not really work with jupyter notebooks, because the kernel remembers the increment
        Player.id_counter += 1        
    
    def __dir__(self) -> list:
        """Implementation for serialization and logging

        Returns:
            list: List of all fields relevant for serialization. 
        """
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

def _create_and_shuffle_damage_cards(node_indices:list(int)=None, number_of_jokers:int = 4) -> list[int]:
    """Emulate a shuffled standard deck of 1 to 21 with two jokers (=0) and only one color

    Returns:
            list[int]: shuffled standard deck of 23 cards
    """
    damage_cards = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18] if not node_indices else node_indices
    damage_cards + [0 for i in range(number_of_jokers)]
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
