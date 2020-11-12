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
        self.currentPlayer = None
        self.target_card = None

    def get_next_player(self) -> Player:
        player_index = self.players.index(self.currentPlayer)
        return self.players[(player_index + 1) % len(self.players)]

        
    def prepare_game(self): 
        # Prepare card stacks
        self.board.damage_cards = self.create_and_shuffle_damage_cards()
        self.board.player_cards = self.create_and_shuffle_player_cards()
        # Damage nodes 
        self.damage_nodes() 
        # Choose target card at random and make deep copy to avoid errors
        target_card = Game.targetCards[random.randint(0, len(Game.targetCards)-1)]
        self.target_card = TargetCard(target_card.start_index, target_card.destination_index, target_card.amount)
        # Position 2 freight units at start node 
        self.board.get_node_by_index(self.target_card.start_index).freight = 2
        # Distribute player funds
        self.set_player_funds()
        # Set first Industry Player to begin
        self.currentPlayer = self.players[0]
        # Game is prepared 
        self.isPrepared = True 


    def iterate(self): 
        while not self.isWon and not self.isLost:
            for currentPlayer in self.players:
                # 1 action phase
                while currentPlayer.actions_left > 0:
                    # perform action placeholder
                    user_input = input(f"Player {self.players.index(currentPlayer)} has {currentPlayer.actions_left} actions left. Press any key.")
                    currentPlayer.actions_left = currentPlayer.actions_left - 1
                # 2 resupply phase 
                for i in range(0,2): 
                    if self.board.draw_player_card() is 1:
                        currentPlayer.funds += 1
                    else: 
                        # 2.1 destruction quota up 
                        self.board.destruction_level = self.board.destruction_level + 1
                        # 2.2 unexpected string damage
                        damage_card = self.board.draw_damage_card('bottom')
                        if damage_card is not 0:
                            current_node = self.board.get_node_by_index(damage_card)
                            current_node.add_damage(3)
                        # 2.3 increase intensity
                        random.shuffle(self.board.damage_cards_discards) 
                        self.board.damage_cards += self.board.damage_cards_discards
                        self.board.damage_cards_discards = [] 
                # discard cards if more than 7 in the hand
                currentPlayer.funds = 7 if currentPlayer.funds > 7 else currentPlayer.funds 
                # 3 damage phase
                destruction_level_to_card_draw_mapping = {0:1, 1:1, 2:2, 3:2, 4:3}
                for i in range(0, destruction_level_to_card_draw_mapping[self.board.destruction_level]):
                    try:
                        damage_card = self.board.draw_damage_card() 
                        if damage_card is not 0:
                            current_node = self.board.get_node_by_index(damage_card)
                            current_node.add_damage(1)
                    except IndexError: 
                        # no damage cards left special case 
                        # TODO program edge case behavior
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
            result.append(Node(**entry, board=self))
        return result
    
    def get_node_by_index(self, game_index:int) -> Node:
        return self.nodes[game_index - 1]

    def draw_player_card(self, draw_from:str ='top') -> int: 
        if draw_from not in ['top', 'bottom']:
            raise ValueError("from parameter must be 'top' or 'bottom'.")     
        if draw_from is "top":
            card = self.player_cards.pop()
        else:
            card = self.player_cards.pop(0)
        self.player_cards_discards.append(card)
        return card

    def draw_damage_card(self, draw_from:str ='top') -> int:
        if draw_from not in ['top', 'bottom']:
            raise ValueError("from parameter must be 'top' or 'bottom'.")     
        if draw_from is "top":
            card = self.damage_cards.pop()
        else:
            card = self.player_cards.pop(0)
        self.damage_cards_discards.append(card)
        return card


class Node(): 
    def __init__(self, index:int, name:str, node_type:str, neighbors:list[int], board:Board) -> None: 
        self.index = index
        self.name = name
        self.node_type = node_type
        self.neighbors = neighbors
        self.damage = 0 
        self.freight = 0
        self.affected_by_cascade = False
        self.board = board
    
    def add_damage(self, damage_value:int) -> None: 
        self.damage += damage_value
        if self.damage > 3:
            self.damage = 3
            self.cascade_node()
    
    def cascade_node(self) -> None:
        self.affected_by_cascade = True
        self.board.cascade_level += 1
        for node_index in self.neighbors:
            neighbor_node = self.board.get_node_by_index(node_index) 
            if not neighbor_node.affected_by_cascade:
                neighbor_node.add_damage(1)
        self.affected_by_cascade = False

        

    

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
    
    def make_longtime_investment(self): 
        pass

    def coordinate_drivers(self): 
        pass 

class InvalidActionException(Exception):
    def __init__(self, player:Player, message:str=""):
        self.player = player
        self.message = message 


g = Game()
g.prepare_game()
g.iterate()