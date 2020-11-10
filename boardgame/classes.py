#important to allow for return type of classes, see https://stackoverflow.com/questions/33533148/how-do-i-type-hint-a-method-with-the-type-of-the-enclosing-class
from __future__ import annotations
import json
import random
import math

class TargetCard(): 
    def __init__(self, start_index:int, destination_index:int, amount:int) -> None:
        self.start_index = start_index
        self.destination_index = destination_index
        self.amount = amount
        
class Game(): 

    targetCards = [
        TargetCard(19, 21, 3),  # Marl to Dortmund
        TargetCard(12, 20, 3)   # RHK to Trianel
    ]

    def __init__(self, random_seed:int = None) -> None: 
        if random_seed is not None:
            random.seed(random_seed)
        self.isWon = False 
        self.isLost = False 
        self.isPrepared = False
        self.turn = 0
        self.board = Board()
        self.players =[
            IndustryPlayer(self), 
            InvestorPlayer(self), 
            DriverPlayer(self), 
            DriverPlayer(self), 
        ]
        self.target_card = None
        
    def prepare_game(self): 
        # Prepare card stacks
        self.board.damage_cards = self.create_and_shuffle_damage_cards()
        self.board.player_cards = self.create_and_shuffle_player_cards()
        # Damage nodes 
        self.damage_nodes() 
        # Choose target card at random and make deep copy to avoid errors
        target_card = Game.targetCards[random.randint(0, len(Game.targetCards))]
        self.target_card = TargetCard(target_card.start_index, target_card.destination_index, target_card.amount)
        # Position 2 freight units at start node 
        self.board.get_node_by_index(self.target_card.start_index).freight = 2
        # Distribute player funds
        self.set_player_funds()
        # Game is prepared 
        self.isPrepared = True 


    def iterate(self): 
        pass

    def create_and_shuffle_damage_cards(self) -> list[int]:
        """Emulate a shuffled standard deck of 1 to 21 with two jokers (=0) and only one color

        Returns:
            list[int]: shuffled standard deck of 23 cards
        """
        damage_cards = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 0, 0, 0, 0, 0]
        random.shuffle(damage_cards)
        return damage_cards

    def create_and_shuffle_player_cards(self, number_of_fund_cards:int = 56, number_of_damage_cards:int = 4) -> list[int]: 
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

    def damage_nodes(self) -> None:
        for damage_points in range (1,4): 
            node_index = self.board.damage_cards.pop(0)
            #TODO change indexes to start at 0 and correspond to array positions
            if node_index in range(1, len(self.board.nodes) + 1):
                self.board.nodes[node_index].damage = damage_points
            self.board.damage_cards_discards.append(node_index)
    
    def set_player_funds(self, funds:int = 2) -> None: 
        for player in self.players:
            player.funds = funds

    

class Board():   
    def __init__(self) -> None: 
        self.cascade_level = 0
        self.destruction_level = 0 
        self.damage_cards = []
        self.damage_cards_discards = []
        self.player_cards = []
        self.player_cards_discards = []
        self.nodes = self._load_nodes_from_json()
    
    def _load_nodes_from_json(self, path_to_json:str ="boardgame/map.json") -> list[Node]: 
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
    
    def get_node_by_index(self, game_index:int) -> Node:
        return self.nodes[game_index - 1]




class Node(): 
    def __init__(self, index:int, name:str = "", node_type:str = "green", neighbors:list[int] = []) -> None: 
        self.index = index
        self.name = name
        self.node_type = node_type
        self.neighbors = neighbors
        self.damage = 0 
        self.freight = 0


    

#player and player subclasses
#TODO implement base class as abstract base class https://www.python-course.eu/python3_abstract_classes.php 
class Player(): 
    
    def __init__(self, game:Game, location_index:int=1, funds:int=0) -> None:
        self.game = game
        self.location_index = location_index
        self.funds = funds
        self.actions_left = 4 

    def run(self, destination_index:int) -> None: 
        current_node = self.game.board.get_node_by_index(self.location_index)
        if destination_index not in current_node.neighbors:
            raise InvalidActionException(self)
        self.location_index = destination_index 
        
    
    def fly(self, destination_index:int) -> None: 
        current_node = self.game.board.get_node_by_index(self.location_index)
        valid_destination_indices = [node.index for node in self.game.board.nodes if node.node_type in ['orange']]
        if destination_index not in valid_destination_indices:
            raise InvalidActionException(self)
        if self.funds < 2:
            raise InvalidActionException(self)
        self.location_index = destination_index
        self.funds = self.funds -2
        
    
    def special_flight(self, destination_index:int) -> None: 
        valid_destination_indices = [node.index for node in self.game.board.nodes if node.node_type in ['purple']]
        if destination_index not in valid_destination_indices:
            raise InvalidActionException(self)
        self.location_index = destination_index
        

class DriverPlayer(Player):
    def share_resources(self, otherPlayer:Player) -> None:
        if self.funds < 1: 
            raise InvalidActionException(self)
        if otherPlayer.location_index != self.location_index:
            raise InvalidActionException(self) 
        self.funds = self.funds -1 
        otherPlayer.funds = otherPlayer.funds + 1 
            
    
    def repair(self) -> None: 
        current_node = self.game.board.get_node_by_index(self.location_index)
        if self.funds < 1: 
            raise InvalidActionException(self)
        if current_node.damage < 1: 
            raise InvalidActionException(self) 
        self.funds = self.funds - 1
        current_node.damage = current_node.damage - 1
            


class IndustryPlayer(Player):
    def generate_goods(self): 
        current_node = self.game.board.get_node_by_index(self.location_index)
        if self.funds < 2: 
            raise InvalidActionException(self) 
        if current_node.freight >= 3: 
            raise InvalidActionException(self) 
        self.funds = self.funds -2
        current_node.freight = current_node.freight + 1
            
    
    def transport_goods(self, destination_index:int): 
        # substitutes movement action "run" 
        current_node = self.game.board.get_node_by_index(self.location_index)
        destination_node = self.game.board.get_node_by_index(destination_index)
        # cost for the action (because it can cost two if the damage is high enough)
        action_cost = 1
        if current_node.damage == 2: 
            action_cost = 2
        if current_node.freight < 1:
            raise InvalidActionException(self)
        if current_node.damage >= 3:
            raise InvalidActionException(self)
        if action_cost > self.actions_left: 
            raise InvalidActionException(self)

        self.actions_left = self.actions_left - 1 # one action is always substracted
        current_node.freight = current_node.freight -1
        destination_node.freight = destination_node.freight  + 1
        self.run(destination_index)


class InvestorPlayer(Player): 
    def share_resources(self, otherPlayer:Player) -> None:
        if self.funds < 1: 
            raise InvalidActionException(self)
        if otherPlayer.location_index != self.location_index:
            raise InvalidActionException(self) 
        self.funds = self.funds -1 
        otherPlayer.funds = otherPlayer.funds + 1

class InvalidActionException(Exception):
    def __init__(self, player:Player, message:str=""):
        self.player = player
        self.message = message 


